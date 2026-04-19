import discord
from discord.ext import commands
import os
import pikepdf
import string
import asyncio
import tempfile
import pdf_service
from dotenv import load_dotenv

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='pdf ', intents=intents, help_command=None)

MAX_FILE_SIZE_MB = 25
MAX_PAGES = 20  # Prevents huge PDFs from being processed

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

@bot.command(name='help')
async def help_command(ctx):
    help_text = """
**📄 PDF Processing Bot Commands**
`pdf ocr` - Extract text from a PDF file using OCR
`pdf unlock <password>` - Unlock a password-protected PDF
`pdf bruteforce` - Attempt to unlock a PDF using brute force
`pdf help` - Show this help message

**Note:** Attach a PDF to your message when using these commands.
    """
    await ctx.send(help_text)

async def download_attachment(attachment, temp_dir):
    file_path = os.path.join(temp_dir, attachment.filename)
    await attachment.save(file_path)
    return file_path

def is_valid_pdf(attachment):
    return attachment.filename.lower().endswith(".pdf") and attachment.size <= MAX_FILE_SIZE_MB * 1024 * 1024

@bot.command(name='ocr')
async def ocr_command(ctx):
    if not ctx.message.attachments or not is_valid_pdf(ctx.message.attachments[0]):
        await ctx.send(f"❌ Please attach a valid PDF file (≤{MAX_FILE_SIZE_MB}MB)!")
        return

    attachment = ctx.message.attachments[0]
    msg = await ctx.send("⏳ Processing PDF with OCR...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_path = await download_attachment(attachment, temp_dir)

            def process():
                return pdf_service.process_ocr(pdf_path, temp_dir, max_pages=MAX_PAGES)

            text_path = await asyncio.to_thread(process)
            await msg.edit(content="✅ Text extraction complete!")
            await ctx.send(file=discord.File(text_path))

        except Exception as e:
            await msg.edit(content=f"❌ Error: {str(e)}")

@bot.command(name='unlock')
async def unlock_command(ctx, password: str):
    if not ctx.message.attachments or not is_valid_pdf(ctx.message.attachments[0]):
        await ctx.send(f"❌ Please attach a valid PDF file (≤{MAX_FILE_SIZE_MB}MB)!")
        return

    attachment = ctx.message.attachments[0]
    msg = await ctx.send("🔓 Attempting to unlock PDF...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_path = await download_attachment(attachment, temp_dir)

            def unlock():
                return pdf_service.unlock_pdf(pdf_path, password, temp_dir)

            unlocked_path = await asyncio.to_thread(unlock)
            await msg.edit(content="✅ PDF unlocked successfully!")
            await ctx.send(file=discord.File(unlocked_path))

        except pikepdf.PasswordError:
            await msg.edit(content="❌ Incorrect password!")
        except Exception as e:
            await msg.edit(content=f"❌ Error: {str(e)}")

@bot.command(name='bruteforce')
async def bruteforce_command(ctx):
    if not ctx.message.attachments or not is_valid_pdf(ctx.message.attachments[0]):
        await ctx.send(f"❌ Please attach a valid PDF file (≤{MAX_FILE_SIZE_MB}MB)!")
        return

    attachment = ctx.message.attachments[0]
    msg = await ctx.send("🛠 Starting brute force attempt...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            pdf_path = await download_attachment(attachment, temp_dir)
            characters = string.ascii_letters + string.digits
            def brute_force():
                def update_progress(current, total):
                    progress = (current / total) * 100
                    asyncio.run_coroutine_threadsafe(msg.edit(content=f"🔍 Trying passwords... {progress:.2f}%"), bot.loop)
                
                return pdf_service.brute_force_pdf(
                    pdf_path=pdf_path,
                    export_dir=temp_dir,
                    max_length=4,
                    charset=None,
                    progress_callback=update_progress
                )

            password, unlocked_path = await asyncio.to_thread(brute_force)

            if password:
                await msg.edit(content=f"✅ Password found: `{password}`")
                await ctx.send(file=discord.File(unlocked_path))
            else:
                await msg.edit(content="❌ Failed to find the password.")

        except Exception as e:
            await msg.edit(content=f"❌ Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ Error: No token found in .env file!")
        exit(1)
    bot.run(TOKEN)
