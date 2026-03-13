#!/usr/bin/env python3
"""
Test to verify the tuple structure fix for images_to_analyze
"""

# Simulate the images_to_analyze list with mixed tuple lengths
images_to_analyze = [
    (0, b"image_data_1", "Page 1, Image 1", 123),  # Embedded image with xref
    (1, b"image_data_2", "Page 2 (full page scan)", None),  # Full page scan without xref
    (2, b"image_data_3", "Page 3, Image 1", 456),  # Embedded image with xref
    (3, b"image_data_4", "Page 4 (full page scan)", None),  # Full page scan without xref
]

xref_page_count = {
    123: 1,  # Appears on 1 page
    456: 3,  # Appears on 3 pages (template candidate)
}

total_pages = 4

# Test the filtering logic
print("Testing tuple filtering logic...")
print(f"Before filter: {len(images_to_analyze)} images")

filtered = [
    img for img in images_to_analyze
    # Keep if: no xref (full page scan) OR xref appears on <50% of pages
    if img[3] is None or xref_page_count.get(img[3], 1) < total_pages * 0.5
]

print(f"After filter: {len(filtered)} images")
print("\nFiltered images:")
for img in filtered:
    xref = img[3]
    if xref is None:
        print(f"  - {img[2]} (full page scan, no xref)")
    else:
        count = xref_page_count.get(xref, 1)
        print(f"  - {img[2]} (xref={xref}, appears on {count} pages)")

print("\nFiltered out:")
for img in images_to_analyze:
    if img not in filtered:
        xref = img[3]
        count = xref_page_count.get(xref, 1)
        print(f"  - {img[2]} (xref={xref}, appears on {count} pages = {count/total_pages*100:.0f}% of pages)")

# Verify expected results
expected_filtered = 3  # Should keep: img1 (xref=123, 1 page), img2 (None), img4 (None)
                       # Should filter: img3 (xref=456, 3 pages = 75% > 50%)

if len(filtered) == expected_filtered:
    print(f"\n✅ TEST PASSED: Filtered {len(filtered)} images as expected")
    exit(0)
else:
    print(f"\n❌ TEST FAILED: Expected {expected_filtered} images, got {len(filtered)}")
    exit(1)
