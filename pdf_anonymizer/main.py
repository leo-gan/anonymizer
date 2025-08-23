from pdf_anonymizer.cli import app, run

# Register the run function as a command
app.command()(run)

if __name__ == "__main__":
    app()
