# Read the style.css file and inject the logo-circle CSS at the end
with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

logo_circle_css = '''
/* Urban Platter Logo Circle Styling */
.logo-circle {
    width: 180px;              /* Adjust to control circle size */
    height: 180px;             /* Keep width = height for perfect circle */
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    margin: 0 auto;
    overflow: hidden;
    position: relative;
}

.logo-circle img {
    max-width: 85%;           /* Ensures logo stays inside the circle */
    max-height: 85%;          /* Ensures vertical fit and no cropping */
    object-fit: contain;      /* maintains aspect ratio, never crops/stretches */
    display: block;
    margin: 0 auto;
    border-radius: 0;
}
'''

# Append or update the logo styles at the end
css = css.strip() + '\n' + logo_circle_css + '\n'

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('Logo size and circular fit CSS has been added to style.css!')