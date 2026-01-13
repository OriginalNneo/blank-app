from rembg import remove
from PIL import Image
import io

input_path = 'Image/TGYN Logo S.jpeg'
output_path = 'Image/logo_nobg.png'

try:
    with open(input_path, 'rb') as i:
        input_data = i.read()
        output_data = remove(input_data)
        
    with open(output_path, 'wb') as o:
        o.write(output_data)
        
    print(f"Successfully removed background and saved to {output_path}")
except Exception as e:
    print(f"Error processing image: {e}")
