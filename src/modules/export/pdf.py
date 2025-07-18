import aiofiles
import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .file_operations import generateName
from ..utils.log import logError


async def save_to_pdf(found_accounts, result_type, config):
    """Asynchronously generates a PDF report and saves it to a file."""
    regular_font_file = os.path.join(
        os.getcwd(),
        config.ASSETS_DIRECTORY,
        config.FONTS_DIRECTORY,
        config.FONT_REGULAR_FILE,
    )
    bold_font_file = os.path.join(
        os.getcwd(),
        config.ASSETS_DIRECTORY,
        config.FONTS_DIRECTORY,
        config.FONT_BOLD_FILE,
    )

    try:
        registerFont(TTFont(config.FONT_NAME_REGULAR, regular_font_file))
        registerFont(TTFont(config.FONT_NAME_BOLD, bold_font_file))

        file_name = generateName(config, "pdf")
        path = os.path.join(config.saveDirectory, file_name)

        buffer = io.BytesIO()
        width, height = letter
        c = canvas.Canvas(buffer, pagesize=letter)

        # This part is synchronous and CPU-bound (reportlab)
        _generate_pdf_content(c, found_accounts, result_type, config, width, height)
        c.save()

        pdf_data = buffer.getvalue()
        buffer.close()

        async with aiofiles.open(path, "wb") as f:
            await f.write(pdf_data)

        config.console.print(f"  Saved results to '[cyan1]{file_name}[/cyan1]'")
        return True
    except Exception as e:
        logError(e, "Couldn't save results to PDF file!", config)
        return False


def _generate_pdf_content(c, found_accounts, result_type, config, width, height):
    """Helper function to generate the PDF content synchronously."""
    accounts_count = len(found_accounts)

    # * Header
    c.drawImage(
        os.path.join(
            os.getcwd(),
            config.ASSETS_DIRECTORY,
            config.IMAGES_DIRECTORY,
            "blackbird-logo.png",
        ),
        35, height - 90, width=60, height=60
    )
    c.setFont(config.FONT_NAME_BOLD, 15)
    c.drawCentredString((width / 2) - 5, height - 70, "Report")
    c.setFont(config.FONT_NAME_REGULAR, 7)
    c.drawString(width - 90, height - 70, config.datePretty)
    c.setFont(config.FONT_NAME_REGULAR, 5)
    c.drawString(width - 185, height - 25, "This report was generated using the Blackbird OSINT Tool.")

    # * Identifier Box
    c.setFillColor("#EDEBED")
    c.setStrokeColor("#BAB8BA")
    c.rect(40, height - 160, 530, 35, stroke=1, fill=1)
    c.setFillColor("#000000")
    identifier = config.currentUser if result_type == "username" else config.currentEmail
    identifier_width = stringWidth(identifier, config.FONT_NAME_BOLD, 11)
    c.drawImage(
        os.path.join(os.getcwd(), config.ASSETS_DIRECTORY, config.IMAGES_DIRECTORY, "correct.png"),
        (width / 2) - ((identifier_width / 2) + 15), height - 147, width=10, height=10, mask="auto"
    )
    c.setFont(config.FONT_NAME_BOLD, 11)
    c.drawCentredString(width / 2, height - 145, identifier)

    # * Warning Box
    c.setFillColor("#FFF8C5")
    c.setStrokeColor("#D9C884")
    c.rect(40, height - 210, 530, 35, stroke=1, fill=1)
    c.setFillColor("#57523f")
    c.setFont(config.FONT_NAME_REGULAR, 8)
    c.drawImage(
        os.path.join(os.getcwd(), config.ASSETS_DIRECTORY, config.IMAGES_DIRECTORY, "warning.png"),
        55, height - 197, width=10, height=10, mask="auto"
    )
    c.drawString(70, height - 195, "Blackbird can make mistakes. Consider checking the information.")

    y_pos = height - 240

    # * AI Analysis Section
    if config.ai_analysis:
        _draw_ai_analysis(c, config, y_pos)
        y_pos -= 335 # Adjust space for AI section

    # * Results Section
    if accounts_count > 0:
        _draw_results(c, found_accounts, config, y_pos, width, height)


def _draw_ai_analysis(c, config, y_pos):
    """Draws the AI analysis section."""
    c.setFillColor("#F4F6F8")
    c.setStrokeColor("#D0D5DA")
    c.rect(40, y_pos - 305, 530, 320, stroke=1, fill=1)
    c.setFillColor("#000000")

    c.drawImage(
        os.path.join(os.getcwd(), config.ASSETS_DIRECTORY, config.IMAGES_DIRECTORY, "ai-stars.png"),
        55, y_pos, width=12, height=12, mask="auto"
    )
    c.setFont(config.FONT_NAME_BOLD, 10)
    c.drawString(70, y_pos + 3, "AI Analysis - Behavioral Summary")
    y_pos -= 15
    c.setFont(config.FONT_NAME_REGULAR, 8)
    c.drawString(55, y_pos, "This behavioral summary was generated using AI based on the detected online presence.")
    y_pos -= 15

    # Helper to draw a text block
    def _draw_text_block(c, title, content, y_pos, is_list=False):
        c.setFont(config.FONT_NAME_BOLD, 10)
        c.drawString(55, y_pos, title)
        y_pos -= 12
        c.setFont(config.FONT_NAME_REGULAR, 8)
        if is_list:
            for item in content:
                c.drawString(55, y_pos, f"- {item}")
                y_pos -= 10
        else:
            lines = simpleSplit(content, config.FONT_NAME_REGULAR, 8, 510)
            text = c.beginText(55, y_pos)
            for line in lines:
                text.textLine(line)
                y_pos -= 10
            c.drawText(text)
        return y_pos - 5

    if config.ai_analysis.get("summary"):
        y_pos = _draw_text_block(c, "Summary", config.ai_analysis["summary"], y_pos)
    if config.ai_analysis.get("categorization"):
        y_pos = _draw_text_block(c, "Categorization", config.ai_analysis["categorization"], y_pos)
    if config.ai_analysis.get("insights"):
        y_pos = _draw_text_block(c, "Insights", config.ai_analysis["insights"], y_pos, is_list=True)
    if config.ai_analysis.get("risk_flags"):
        y_pos = _draw_text_block(c, "Risk Flags", config.ai_analysis["risk_flags"], y_pos, is_list=True)
    if config.ai_analysis.get("tags"):
        y_pos = _draw_text_block(c, "Tags", config.ai_analysis["tags"], y_pos, is_list=True)


def _draw_results(c, found_accounts, config, y_pos, width, height):
    """Draws the found accounts section."""
    c.setFillColor("#000000")
    c.setFont(config.FONT_NAME_REGULAR, 15)
    c.drawImage(
        os.path.join(os.getcwd(), config.ASSETS_DIRECTORY, config.IMAGES_DIRECTORY, "arrow.png"),
        40, y_pos, width=12, height=12, mask="auto"
    )
    c.drawString(55, y_pos, f"Results ({len(found_accounts)})")
    y_pos -= 25

    for result in found_accounts:
        if y_pos < 70:
            c.showPage()
            y_pos = height - 50

        c.setFont(config.FONT_NAME_BOLD, 12)
        c.drawString(72, y_pos, result['name'])

        site_width = stringWidth(result['name'], config.FONT_NAME_BOLD, 12)
        c.drawImage(
            os.path.join(os.getcwd(), config.ASSETS_DIRECTORY, config.IMAGES_DIRECTORY, "link.png"),
            77 + site_width, y_pos, width=10, height=10, mask="auto"
        )
        c.linkURL(result["url"], (77 + site_width, y_pos, 87 + site_width, y_pos + 10), relative=1)
        y_pos -= 15

        if result.get("metadata"):
            c.setFont(config.FONT_NAME_REGULAR, 7)
            for data in result["metadata"]:
                if y_pos < 70:
                    c.showPage()
                    y_pos = height - 50
                
                if data["type"] == "String":
                    metadata_str = f"{data['name']}: {data['value']}"
                    metadata_width = stringWidth(metadata_str, config.FONT_NAME_REGULAR, 7)
                    c.setFillColor("#EDEBED")
                    c.roundRect(90, y_pos - 4, metadata_width + 10, 13, 6, fill=1, stroke=0)
                    c.setFillColor("#000000")
                    c.drawString(95, y_pos, metadata_str)
                    y_pos -= 15

        y_pos -= 10
