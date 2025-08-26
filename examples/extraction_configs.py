"""
Advanced extraction configuration examples.

This file contains various extraction configurations for different types of websites
and use cases, demonstrating the flexibility of the scraping system.
"""

# E-commerce product extraction
ECOMMERCE_CONFIG = {
    "product_name": {
        "selector": "h1.product-title, .product-name h1, [data-testid='product-name']",
        "attr": "text",
        "multiple": False
    },
    "price": {
        "selector": ".price, .product-price, [data-testid='price']",
        "attr": "text",
        "multiple": False
    },
    "description": {
        "selector": ".product-description, .description, [data-testid='description']",
        "attr": "text",
        "multiple": False
    },
    "images": {
        "selector": ".product-image img, .gallery img",
        "attr": "src",
        "multiple": True
    },
    "availability": {
        "selector": ".availability, .stock-status, [data-testid='availability']",
        "attr": "text",
        "multiple": False
    },
    "rating": {
        "selector": ".rating, .stars, [data-testid='rating']",
        "attr": "text",
        "multiple": False
    },
    "specifications": {
        "selector": ".specifications li, .specs .spec-item",
        "attr": "text",
        "multiple": True
    }
}

# News article extraction
NEWS_ARTICLE_CONFIG = {
    "headline": {
        "selector": "h1, .headline, .article-title",
        "attr": "text",
        "multiple": False
    },
    "author": {
        "selector": ".author, .byline, [rel='author']",
        "attr": "text",
        "multiple": False
    },
    "publish_date": {
        "selector": "time, .date, .published-date",
        "attr": "datetime",
        "multiple": False
    },
    "article_body": {
        "selector": ".article-body p, .content p, .post-content p",
        "attr": "text",
        "multiple": True
    },
    "tags": {
        "selector": ".tags a, .categories a",
        "attr": "text",
        "multiple": True
    },
    "featured_image": {
        "selector": ".featured-image img, .article-image img",
        "attr": "src",
        "multiple": False
    }
}

# Social media profile extraction
SOCIAL_PROFILE_CONFIG = {
    "username": {
        "selector": ".username, .handle, .profile-username",
        "attr": "text",
        "multiple": False
    },
    "display_name": {
        "selector": ".display-name, .profile-name, h1",
        "attr": "text",
        "multiple": False
    },
    "bio": {
        "selector": ".bio, .description, .profile-description",
        "attr": "text",
        "multiple": False
    },
    "follower_count": {
        "selector": ".followers-count, .follower-stats",
        "attr": "text",
        "multiple": False
    },
    "following_count": {
        "selector": ".following-count, .following-stats",
        "attr": "text",
        "multiple": False
    },
    "posts": {
        "selector": ".post, .tweet, .update",
        "attr": "text",
        "multiple": True
    },
    "profile_image": {
        "selector": ".profile-image img, .avatar img",
        "attr": "src",
        "multiple": False
    }
}

# Job listing extraction
JOB_LISTING_CONFIG = {
    "job_title": {
        "selector": "h1, .job-title, .position-title",
        "attr": "text",
        "multiple": False
    },
    "company_name": {
        "selector": ".company-name, .employer, .company",
        "attr": "text",
        "multiple": False
    },
    "location": {
        "selector": ".location, .job-location",
        "attr": "text",
        "multiple": False
    },
    "salary": {
        "selector": ".salary, .pay, .compensation",
        "attr": "text",
        "multiple": False
    },
    "job_type": {
        "selector": ".job-type, .employment-type",
        "attr": "text",
        "multiple": False
    },
    "description": {
        "selector": ".job-description, .description",
        "attr": "text",
        "multiple": False
    },
    "requirements": {
        "selector": ".requirements li, .qualifications li",
        "attr": "text",
        "multiple": True
    },
    "benefits": {
        "selector": ".benefits li, .perks li",
        "attr": "text",
        "multiple": True
    },
    "posted_date": {
        "selector": ".posted-date, .job-date, time",
        "attr": "text",
        "multiple": False
    }
}

# Real estate listing extraction
REAL_ESTATE_CONFIG = {
    "property_title": {
        "selector": "h1, .property-title, .listing-title",
        "attr": "text",
        "multiple": False
    },
    "price": {
        "selector": ".price, .property-price, .listing-price",
        "attr": "text",
        "multiple": False
    },
    "address": {
        "selector": ".address, .property-address, .location",
        "attr": "text",
        "multiple": False
    },
    "bedrooms": {
        "selector": ".bedrooms, .beds, [data-testid='bedrooms']",
        "attr": "text",
        "multiple": False
    },
    "bathrooms": {
        "selector": ".bathrooms, .baths, [data-testid='bathrooms']",
        "attr": "text",
        "multiple": False
    },
    "square_footage": {
        "selector": ".square-feet, .sqft, .area",
        "attr": "text",
        "multiple": False
    },
    "description": {
        "selector": ".property-description, .listing-description",
        "attr": "text",
        "multiple": False
    },
    "features": {
        "selector": ".features li, .amenities li",
        "attr": "text",
        "multiple": True
    },
    "images": {
        "selector": ".property-images img, .listing-photos img",
        "attr": "src",
        "multiple": True
    },
    "agent_info": {
        "selector": ".agent-name, .realtor-name",
        "attr": "text",
        "multiple": False
    }
}

# Restaurant menu extraction
RESTAURANT_MENU_CONFIG = {
    "restaurant_name": {
        "selector": "h1, .restaurant-name, .business-name",
        "attr": "text",
        "multiple": False
    },
    "menu_categories": {
        "selector": ".menu-category, .category-title",
        "attr": "text",
        "multiple": True
    },
    "menu_items": {
        "selector": ".menu-item",
        "attr": "outerHTML",  # Get full HTML to parse item details
        "multiple": True
    },
    "item_names": {
        "selector": ".item-name, .dish-name",
        "attr": "text",
        "multiple": True
    },
    "item_prices": {
        "selector": ".item-price, .price",
        "attr": "text",
        "multiple": True
    },
    "item_descriptions": {
        "selector": ".item-description, .dish-description",
        "attr": "text",
        "multiple": True
    },
    "contact_info": {
        "selector": ".contact, .phone, .address",
        "attr": "text",
        "multiple": True
    }
}

# Academic paper/research extraction
ACADEMIC_PAPER_CONFIG = {
    "title": {
        "selector": "h1, .article-title, .paper-title",
        "attr": "text",
        "multiple": False
    },
    "authors": {
        "selector": ".authors .author, .author-list .author",
        "attr": "text",
        "multiple": True
    },
    "abstract": {
        "selector": ".abstract, .summary",
        "attr": "text",
        "multiple": False
    },
    "keywords": {
        "selector": ".keywords .keyword, .tags .tag",
        "attr": "text",
        "multiple": True
    },
    "publication_date": {
        "selector": ".pub-date, .published, time",
        "attr": "text",
        "multiple": False
    },
    "journal": {
        "selector": ".journal, .publication",
        "attr": "text",
        "multiple": False
    },
    "doi": {
        "selector": ".doi, [data-doi]",
        "attr": "text",
        "multiple": False
    },
    "citations": {
        "selector": ".citation-count, .citations",
        "attr": "text",
        "multiple": False
    },
    "references": {
        "selector": ".references li, .bibliography li",
        "attr": "text",
        "multiple": True
    }
}

# Forum/discussion extraction
FORUM_POST_CONFIG = {
    "thread_title": {
        "selector": "h1, .thread-title, .topic-title",
        "attr": "text",
        "multiple": False
    },
    "original_post": {
        "selector": ".original-post .content, .first-post .message",
        "attr": "text",
        "multiple": False
    },
    "post_author": {
        "selector": ".post-author, .username, .user-name",
        "attr": "text",
        "multiple": False
    },
    "post_date": {
        "selector": ".post-date, .timestamp, time",
        "attr": "text",
        "multiple": False
    },
    "replies": {
        "selector": ".reply .content, .post .message",
        "attr": "text",
        "multiple": True
    },
    "reply_authors": {
        "selector": ".reply .author, .post .username",
        "attr": "text",
        "multiple": True
    },
    "vote_count": {
        "selector": ".votes, .score, .points",
        "attr": "text",
        "multiple": False
    },
    "tags": {
        "selector": ".tags .tag, .categories .category",
        "attr": "text",
        "multiple": True
    }
}

# Event listing extraction
EVENT_LISTING_CONFIG = {
    "event_name": {
        "selector": "h1, .event-title, .event-name",
        "attr": "text",
        "multiple": False
    },
    "event_date": {
        "selector": ".event-date, .date, time",
        "attr": "text",
        "multiple": False
    },
    "event_time": {
        "selector": ".event-time, .time",
        "attr": "text",
        "multiple": False
    },
    "venue": {
        "selector": ".venue, .location, .event-location",
        "attr": "text",
        "multiple": False
    },
    "address": {
        "selector": ".address, .venue-address",
        "attr": "text",
        "multiple": False
    },
    "description": {
        "selector": ".event-description, .description",
        "attr": "text",
        "multiple": False
    },
    "ticket_price": {
        "selector": ".ticket-price, .price",
        "attr": "text",
        "multiple": False
    },
    "organizer": {
        "selector": ".organizer, .event-organizer",
        "attr": "text",
        "multiple": False
    },
    "categories": {
        "selector": ".categories .category, .tags .tag",
        "attr": "text",
        "multiple": True
    }
}

# Contact page extraction
CONTACT_PAGE_CONFIG = {
    "company_name": {
        "selector": "h1, .company-name, .business-name",
        "attr": "text",
        "multiple": False
    },
    "phone_numbers": {
        "selector": ".phone, .tel, [href^='tel:']",
        "attr": "text",
        "multiple": True
    },
    "email_addresses": {
        "selector": ".email, [href^='mailto:']",
        "attr": "href",
        "multiple": True
    },
    "physical_address": {
        "selector": ".address, .location, .contact-address",
        "attr": "text",
        "multiple": False
    },
    "business_hours": {
        "selector": ".hours, .opening-hours, .business-hours",
        "attr": "text",
        "multiple": False
    },
    "social_media": {
        "selector": ".social-links a, .social-media a",
        "attr": "href",
        "multiple": True
    },
    "contact_form": {
        "selector": "form",
        "attr": "outerHTML",
        "multiple": False
    }
}

# Collection of all configs for easy access
EXTRACTION_CONFIGS = {
    "ecommerce": ECOMMERCE_CONFIG,
    "news": NEWS_ARTICLE_CONFIG,
    "social": SOCIAL_PROFILE_CONFIG,
    "jobs": JOB_LISTING_CONFIG,
    "realestate": REAL_ESTATE_CONFIG,
    "restaurant": RESTAURANT_MENU_CONFIG,
    "academic": ACADEMIC_PAPER_CONFIG,
    "forum": FORUM_POST_CONFIG,
    "events": EVENT_LISTING_CONFIG,
    "contact": CONTACT_PAGE_CONFIG
}


def get_config_for_site_type(site_type: str):
    """Get extraction configuration for a specific site type."""
    return EXTRACTION_CONFIGS.get(site_type.lower())


def print_all_configs():
    """Print all available configurations."""
    print("Available extraction configurations:")
    print("=" * 50)
    
    for name, config in EXTRACTION_CONFIGS.items():
        print(f"\n{name.upper()} CONFIG:")
        print("-" * 20)
        
        for field, settings in config.items():
            if isinstance(settings, dict):
                print(f"  {field}: {settings['selector']} ({settings.get('attr', 'text')})")
            else:
                print(f"  {field}: {settings}")


if __name__ == "__main__":
    print_all_configs()