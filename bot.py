import discord
from discord.ext import commands
import os
import pytesseract
from pdf2image import convert_from_path
import pikepdf
import itertools
import string
import asyncio
import tempfile
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
                images = convert_from_path(pdf_path)
                if len(images) > MAX_PAGES:
                    raise ValueError(f"PDF too long ({len(images)} pages). Max allowed: {MAX_PAGES}")

                extracted_text = ""
                for i, img in enumerate(images):
                    extracted_text += f"Page {i+1}:\n{pytesseract.image_to_string(img)}\n" + "="*50 + "\n"

                text_path = os.path.join(temp_dir, "extracted_text.txt")
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                return text_path

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
                pdf = pikepdf.open(pdf_path, password=password)
                output_path = os.path.join(temp_dir, "unlocked.pdf")
                pdf.save(output_path)
                return output_path

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
            found = False

            def brute_force():
                nonlocal found
                total_attempts = sum(len(characters)**l for l in range(1, 5))
                attempt_count = 0

                for length in range(1, 5):
                    for pwd_tuple in itertools.product(characters, repeat=length):
                        password = ''.join(pwd_tuple)
                        attempt_count += 1
                        if attempt_count % 500 == 0:
                            progress = attempt_count / total_attempts * 100
                            asyncio.run_coroutine_threadsafe(msg.edit(content=f"🔍 Trying passwords... {progress:.2f}%"), bot.loop)

                        try:
                            pdf = pikepdf.open(pdf_path, password=password)
                            output_path = os.path.join(temp_dir, "unlocked.pdf")
                            pdf.save(output_path)
                            found = True
                            return password, output_path
                        except pikepdf.PasswordError:
                            continue
                return None, None

            password, unlocked_path = await asyncio.to_thread(brute_force)

            if found:
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
