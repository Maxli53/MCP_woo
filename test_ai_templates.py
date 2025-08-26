#!/usr/bin/env python3
"""
Test AI description templates with multiple languages and styles
"""

def generate_technical_description(product_data, language="en"):
    """Generate technical snowmobile description"""
    
    templates = {
        "en": """The {brand} {model} (SKU: {sku}) is a professional-grade {year} snowmobile engineered for superior performance and reliability.

TECHNICAL SPECIFICATIONS:
• Engine: {engine}
• Track System: {track}
• Color Scheme: {color}
• Starting System: {starter}

This snowmobile delivers exceptional traction and control with its advanced Cobra track technology. The {engine} engine provides optimal power-to-weight ratio for various terrain conditions.

Price: {price}

Ideal for professional riders and serious enthusiasts who demand uncompromising quality and performance in challenging winter conditions.""",

        "no": """Den {brand} {model} (Artikkelnr: {sku}) er en profesjonell {year} snøscooter utviklet for overlegen ytelse og pålitelighet.

TEKNISKE SPESIFIKASJONER:
• Motor: {engine}  
• Beltesystem: {track}
• Fargeskjema: {color}
• Startsystem: {starter}

Denne snøscooteren leverer eksepsjonell trekkraft og kontroll med sin avanserte Cobra-belteteknologi. {engine}-motoren gir optimalt effekt-til-vekt-forhold for ulike terrengforhold.

Pris: {price}

Ideell for profesjonelle kjørere og seriøse entusiaster som krever kompromissløs kvalitet og ytelse under krevende vinterforhold.""",
    }
    
    template = templates.get(language, templates["en"])
    
    return template.format(
        brand=product_data.get('brand', 'N/A'),
        model=product_data.get('model', 'N/A'),
        sku=product_data.get('sku', 'N/A'),
        year=product_data.get('year', 'Current'),
        engine=product_data.get('engine', 'Contact for specifications'),
        track=product_data.get('track', 'Professional track system'),
        color=product_data.get('color', 'Multiple colors available'),
        starter=product_data.get('starter', 'Standard starting system'),
        price=product_data.get('price_fi', 'Contact for pricing')
    )

def generate_marketing_description(product_data, language="en"):
    """Generate marketing-focused description"""
    
    templates = {
        "en": """Experience the thrill of winter with the {brand} {model}!

🏔️ ADVENTURE AWAITS
This stunning {year} {color} snowmobile is your gateway to unforgettable winter adventures. With its powerful {engine} engine and advanced {track} track system, you'll conquer any terrain with confidence.

✨ WHY CHOOSE {brand}?
• Legendary reliability and craftsmanship
• Cutting-edge engineering for peak performance  
• Stunning design that turns heads on the trail
• Trusted by riders worldwide

💰 EXCEPTIONAL VALUE: {price}

Ready to make this winter your most exciting yet? The {brand} {model} is waiting for you!

#SnowmobileLife #WinterAdventure #{brand}""",

        "no": """Opplev vintermoro med {brand} {model}!

🏔️ EVENTYRET VENTER
Denne fantastiske {year} {color} snøscooteren er din port til uforglemmelige vintereventyr. Med sin kraftige {engine}-motor og avanserte {track}-beltesystem, mestrer du ethvert terreng med selvtillit.

✨ HVORFOR VELGE {brand}?
• Legendarisk pålitelighet og håndverk
• Banebrytende ingeniørkunst for toppytelse
• Imponerende design som fanger oppmerksomhet på løypa
• Stolt på av kjørere verden over

💰 EKSEPSJONELL VERDI: {price}

Klar til å gjøre denne vinteren til din mest spennende hittil? {brand} {model} venter på deg!

#SnøscooterLiv #VinterEventyr #{brand}""",
    }
    
    template = templates.get(language, templates["en"])
    
    return template.format(
        brand=product_data.get('brand', 'N/A'),
        model=product_data.get('model', 'N/A'),
        year=product_data.get('year', 'Current'),
        color=product_data.get('color', 'Beautiful'),
        engine=product_data.get('engine', 'powerful'),
        track=product_data.get('track', 'professional-grade'),
        price=product_data.get('price_fi', 'Contact for pricing')
    )

def test_with_real_lynx_data():
    """Test with actual LYNX product data"""
    
    # Real LYNX data from the database
    lynx_products = [
        {
            "sku": "LYRA",
            "brand": "LYNX", 
            "model": "Rave 120",
            "price_fi": "5 000 €",
            "engine": "120cc",
            "track": "67in 0.75in 19mm Cobra",
            "color": "Viper Red",
            "year": 2024,
            "starter": "Manual Start"
        },
        {
            "sku": "LYRB", 
            "brand": "LYNX",
            "model": "Rave 200", 
            "price_fi": "6 650 €",
            "engine": "200cc",
            "track": "93in 1.0in 25mm Cobra",
            "color": "Viper Red",
            "year": 2024,
            "starter": "Electric Start"
        },
        {
            "sku": "SCRA",
            "brand": "LYNX",
            "model": "Rave Enduro",
            "price_fi": "18 350 €", 
            "engine": "600R E-TEC",
            "track": "129in 3300mm 1.6in 41mm Cobra",
            "color": "Bright White / Evo Red",
            "year": 2024,
            "starter": "Electric Start"
        }
    ]
    
    print("=== AI Description Generation Test ===")
    print()
    
    for i, product in enumerate(lynx_products):
        print(f"--- Product {i+1}: {product['sku']} ---")
        
        # Technical description in English
        print("TECHNICAL DESCRIPTION (English):")
        tech_desc = generate_technical_description(product, "en")
        print(tech_desc)
        print()
        
        # Marketing description in Norwegian  
        print("MARKETING DESCRIPTION (Norwegian):")
        marketing_desc = generate_marketing_description(product, "no")
        print(marketing_desc)
        print()
        print("=" * 80)
        print()

if __name__ == "__main__":
    test_with_real_lynx_data()