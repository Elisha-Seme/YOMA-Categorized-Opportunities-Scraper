import os
import requests
import fitz  
from bs4 import BeautifulSoup
from googlesearch import search
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from textwrap import wrap

# folder path
downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
pdf_path = os.path.join(downloads_folder, "YOMA_Categorized_Opportunities.pdf")
text_file_path = os.path.join(downloads_folder, "YOMA_Opportunities_SocialMedia.txt")

# Default categories
default_categories = {
    "Agriculture 🌾": "youth opportunities in agriculture",
    "AI, Data & Analytics 🤖📊": "youth opportunities in AI and Data Science",
    "Business & Entrepreneurship 💼🚀": "business and entrepreneurship programs for youth",
    "Career & Personal Development 🎯📚": "career development opportunities for young professionals",
}

categories = default_categories.copy()

print("\nCategory Selection Options:\n")
print("1️⃣ Use default categories")
print("2️⃣ Add extra categories (default + new ones)")
print("3️⃣ Define a custom category (search only this one)\n")

choice = input("Enter choice (1, 2, or 3): ").strip()

if choice == "2":
    new_category_name = input("Enter the name of the new category: ").strip()
    new_category_query = input("Enter search query for this category: ").strip()
    categories[f"{new_category_name} 🔥"] = new_category_query
    print(f"✅ Added new category: {new_category_name} 🔥")

elif choice == "3":
    categories.clear()
    custom_name = input("Enter the name of your custom category: ").strip()
    custom_query = input("Enter search query for this category: ").strip()
    categories[f"{custom_name} 🔥"] = custom_query
    print(f"✅ Using only category: {custom_name} 🔥")

print("\n🔍 Searching for opportunities in the following categories:")
for cat in categories:
    print(f"   - {cat}")

num_results = 10
max_opportunities = 30
collected_opportunities = 0
opportunities = []
seen_urls = set()
cached_opportunities = set()

def extract_text_from_pdfs():
    """Extracts previously saved opportunities from existing PDFs."""
    global cached_opportunities
    for file in os.listdir(downloads_folder):
        if file.endswith(".pdf") and "YOMA_Categorized_Opportunities" in file:
            pdf_file = os.path.join(downloads_folder, file)
            try:
                doc = fitz.open(pdf_file)
                for page in doc:
                    text = page.get_text("text")
                    for line in text.split("\n"):
                        if "Link:" in line:
                            cached_opportunities.add(line.strip())
            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")

extract_text_from_pdfs()

def scrape_details(url):
    """Scrapes webpage details (title & description) from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No Title"
        description_tag = soup.find("meta", attrs={"name": "description"})
        description = description_tag["content"].strip() if description_tag else "No description available."
        return {"title": title, "description": description, "url": url}
    except Exception:
        return None

for category, query in categories.items():
    if collected_opportunities >= max_opportunities:
        break
    print(f"\n🔍 Searching for: {category}...")
    urls = list(search(query, num_results=num_results))
    for url in urls:
        if collected_opportunities >= max_opportunities:
            break
        if url in seen_urls or f"Link: {url}" in cached_opportunities:
            continue
        details = scrape_details(url)
        if details:
            opportunities.append({"category": category, **details})
            seen_urls.add(url)
            collected_opportunities += 1
            print(f"✅ [{category}] {details['title']}")

if opportunities:
    # Generate PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setTitle("Categorized Opportunities for Young People")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 750, "Opportunities for Young People")
    c.setFont("Helvetica", 12)
    c.drawString(180, 735, "Categorized by Industry")
    c.line(50, 730, 550, 730)

    y_position = 710
    current_category = None

    for opp in opportunities:
        if y_position < 100:
            c.showPage()
            y_position = 750
        if current_category != opp["category"]:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, opp["category"])
            c.line(50, y_position - 5, 550, y_position - 5)
            y_position -= 20
            current_category = opp["category"]
        c.setFont("Helvetica-Bold", 12)
        title_lines = wrap(f"- {opp['title']}", width=80)
        for line in title_lines:
            c.drawString(50, y_position, line)
            y_position -= 15
        c.setFont("Helvetica", 10)
        description_lines = wrap(f"Description: {opp['description'][:250]}...", width=90)
        for line in description_lines:
            c.drawString(50, y_position, line)
            y_position -= 12
        c.setFillColorRGB(0, 0, 1)
        url_lines = wrap(f"Link: {opp['url']}", width=90)
        for line in url_lines:
            c.drawString(50, y_position, line)
            y_position -= 12
        c.setFillColorRGB(0, 0, 0)
        y_position -= 20
    c.save()
    print(f"\n📄 New PDF saved at: {pdf_path}")

    # Generating social media formatted text file(second document for copy pasting)
    def format_opportunity(opp):
        return f"{opp['category']} *{opp['title']}*\n📖 {opp['description'][:200]}...\n🔗 {opp['url']}\n"

    formatted_opportunities = "\n\n".join(format_opportunity(opp) for opp in opportunities)

    with open(text_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(formatted_opportunities)

    print(f"\n📄 Opportunities saved for social media at: {text_file_path}")

else:
    print("\n✅ No new opportunities found. No new PDF generated.")
