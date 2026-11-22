import discord
from discord.ext import commands
import os
import string
import asyncio
import tempfile
import pikepdf
import pdf_service
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="pdf ", intents=intents, help_command=None)

MAX_FILE_SIZE_MB = 25
MAX_PAGES = 20

CHARSET_MAP = {
    "alphanumeric": string.ascii_letters + string.digits,
    "numbers": string.digits,
    "lowercase": string.ascii_lowercase,
    "uppercase": string.ascii_uppercase,
    "letters": string.ascii_letters,
    "all": string.printable.strip(),
}


@bot.event
async def on_ready():
    print(f"\u2705 Logged in as {bot.user.name}")


@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="\U0001f4c4 PDF Processing Bot",
        description="Process PDF files directly in Discord.",
        color=0xFCA311,
    )
    embed.add_field(
        name="Commands",
        value=(
            "`pdf ocr` \u2014 Extract text from a PDF\n"
            "`pdf unlock <password>` \u2014 Unlock a protected PDF\n"
            "`pdf bruteforce [charset]` \u2014 Crack a PDF password\n"
            "`pdf help` \u2014 Show this message"
        ),
        inline=False,
    )
    embed.add_field(
        name="Charsets for bruteforce",
        value=(
            "`alphanumeric` (default), `numbers`, `lowercase`, "
            "`uppercase`, `letters`, `all`"
        ),
        inline=False,
    )
    embed.set_footer(text="Attach a PDF to your message when using commands.")
    await ctx.send(embed=embed)


async def download_attachment(attachment, temp_dir):
    file_path = os.path.join(temp_dir, attachment.filename)
    await attachment.save(file_path)
    return file_path


def is_valid_pdf(attachment):
    return (
        attachment.filename.lower().endswith(".pdf")
        and attachment.size <= MAX_FILE_SIZE_MB * 1024 * 1024
    )


@bot.command(name="ocr")
async def ocr_command(ctx):
    if not ctx.message.attachments or not is_valid_pdf(ctx.message.attachments[0]):
        await ctx.send(
            f"\u274c Please attach a valid PDF file (\u2264{MAX_FILE_SIZE_MB}MB)!"
        )
        return

    attachment = ctx.message.attachments[0]
    msg = await ctx.send("\u23f3 Processing PDF with OCR...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_path = await download_attachment(attachment, temp_dir)

            def process():
                return pdf_service.process_ocr(
                    pdf_path, temp_dir, max_pages=MAX_PAGES
                )

            text_path = await asyncio.to_thread(process)
            await msg.edit(content="\u2705 Text extraction complete!")
            await ctx.send(file=discord.File(text_path))

        except Exception as e:
            await msg.edit(content=f"\u274c Error: {str(e)}")


@bot.command(name="unlock")
async def unlock_command(ctx, password: str):
    if not ctx.message.attachments or not is_valid_pdf(ctx.message.attachments[0]):
        await ctx.send(
            f"\u274c Please attach a valid PDF file (\u2264{MAX_FILE_SIZE_MB}MB)!"
        )
        return

    attachment = ctx.message.attachments[0]
    msg = await ctx.send("\U0001f513 Attempting to unlock PDF...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_path = await download_attachment(attachment, temp_dir)

            def unlock():
                return pdf_service.unlock_pdf(pdf_path, password, temp_dir)

            unlocked_path = await asyncio.to_thread(unlock)
            await msg.edit(content="\u2705 PDF unlocked successfully!")
            await ctx.send(file=discord.File(unlocked_path))

        except pikepdf.PasswordError:
            await msg.edit(content="\u274c Incorrect password!")
        except Exception as e:
            await msg.edit(content=f"\u274c Error: {str(e)}")


@bot.command(name="bruteforce")
async def bruteforce_command(ctx, charset_name: str = "alphanumeric"):
    if not ctx.message.attachments or not is_valid_pdf(ctx.message.attachments[0]):
        await ctx.send(
            f"\u274c Please attach a valid PDF file (\u2264{MAX_FILE_SIZE_MB}MB)!"
        )
        return

    charset = CHARSET_MAP.get(charset_name.lower())
    if charset is None:
        valid = ", ".join(f"`{k}`" for k in CHARSET_MAP)
        await ctx.send(f"\u274c Unknown charset. Valid options: {valid}")
        return

    attachment = ctx.message.attachments[0]
    msg = await ctx.send(
        f"\U0001f6e0 Starting brute force ({charset_name})..."
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_path = await download_attachment(attachment, temp_dir)

            def brute_force():
                def update_progress(current, total, speed, eta):
                    progress = (current / total) * 100
                    asyncio.run_coroutine_threadsafe(
                        msg.edit(
                            content=f"\U0001f50d Trying passwords... {progress:.1f}%"
                        ),
                        bot.loop,
                    )

                return pdf_service.brute_force_pdf(
                    pdf_path=pdf_path,
                    export_dir=temp_dir,
                    max_length=4,
                    charset=charset,
                    progress_callback=update_progress,
                )

            password, unlocked_path = await asyncio.to_thread(brute_force)

            if password:
                await msg.edit(content=f"\u2705 Password found: `{password}`")
                await ctx.send(file=discord.File(unlocked_path))
            else:
                await msg.edit(content="\u274c Failed to find the password.")

        except Exception as e:
            await msg.edit(content=f"\u274c Error: {str(e)}")


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("\u274c Error: No token found in .env file!")
        exit(1)
    bot.run(TOKEN)
