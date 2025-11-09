import subprocess
import tempfile
import pikepdf
import os

def john_crack_pdf(pdf_path, export_path):
    try:
        # Extract .hash file using pdf2john.pl
        hash_file = tempfile.NamedTemporaryFile(delete=False)
        subprocess.run(["perl", "pdf2john.pl", pdf_path], stdout=open(hash_file.name, 'w'))
        
        # Run john on the hash file
        subprocess.run(["john", hash_file.name])
        
        # Read cracked password
        result = subprocess.run(["john", "--show", hash_file.name], capture_output=True, text=True)
        cracked_password = extract_password_from_john_output(result.stdout)
        
        if cracked_password:
            # Unlock PDF with pikepdf
            pdf = pikepdf.open(pdf_path, password=cracked_password)
            unlocked_pdf_path = os.path.join(export_path, "unlocked.pdf")
            pdf.save(unlocked_pdf_path)
            return f"PDF unlocked with password '{cracked_password}' and saved to {unlocked_pdf_path}"
        else:
            return "Password not found by John the Ripper."
    except Exception as e:
        return f"An error occurred: {str(e)}"


def extract_password_from_john_output(output):
    # Parses John the Ripper output to get cracked password
    # John --show format: filename:password
    lines = output.strip().split('\n')
    for line in lines:
        if ':' in line:
            return line.split(':')[1].strip()
    return None
