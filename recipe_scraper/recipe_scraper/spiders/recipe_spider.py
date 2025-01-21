import scrapy
from datetime import datetime
from urllib.parse import urljoin

class RecipeSpider(scrapy.Spider):
    name = "recipes"
    allowed_domains = ["resepichenom.com"]
    start_urls = ["https://resepichenom.com/kategori/ayam"]

    def parse(self, response):
        # Extract all recipe links
        recipe_links = response.css("article h2 a::attr(href)").getall()

        for link in recipe_links:
            # Build absolute URL and send request to scrape details
            recipe_url = urljoin(response.url, link)
            yield scrapy.Request(url=recipe_url, callback=self.parse_recipe_details)

    def parse_recipe_details(self, response):
        # Extract details from the recipe page
        title = response.css("h1::text").get()
        masa_penyediaan = response.xpath('//p[contains(text(), "Masa Penyediaan")]/following-sibling::p/text()').get()
        masa_memasak = response.xpath('//p[contains(text(), "Masa Memasak")]/following-sibling::p/text()').get()
        jumlah_masa = response.xpath('//p[contains(text(), "Jumlah Masa")]/following-sibling::p/text()').get()
        hidangan = response.xpath('//p[contains(text(), "Hidangan")]/following-sibling::p/text()').get()
        image_url = response.css("div.recipe-card img::attr(src)").get()

        yield {
            "title": title.strip() if title else None,
            "recipe_url": response.url,
            "masa_penyediaan": masa_penyediaan.strip() if masa_penyediaan else None,
            "masa_memasak": masa_memasak.strip() if masa_memasak else None,
            "jumlah_masa": jumlah_masa.strip() if jumlah_masa else None,
            "hidangan": hidangan.strip() if hidangan else None,
            "image_url": urljoin(response.url, image_url) if image_url else None,
            "scraped_at": datetime.now().isoformat()
        }
