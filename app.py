from flask import Flask, jsonify, request
from flask_cors import CORS
from deepface import DeepFace
import os
import supabase

app = Flask(__name__)
origins = os.getenv('FRONTEND_URLS', '').split(',')
CORS(app, resources={r"/*": {"origins": origins}})

DOWNLOAD_PATH = 'download'
IMAGE_FORMATTING = 'jpg'

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def save_files_locally(target: str) -> str:
  client = supabase.create_client(os.getenv("BUCKET_URL"), os.getenv("BUCKET_KEY"))

  response = client.storage.from_(os.getenv("BUCKET_STORAGE")).download(f'{target}.jpg')
  img_path = f'{DOWNLOAD_PATH}/{target}.{IMAGE_FORMATTING}'

  with open(img_path, 'wb') as f:
    f.write(response)
  return img_path 

def validate(user_img: str, wally_img: str, encounter_img: str) -> bool:  
  for i in range(2):
    try:
      obj = DeepFace.verify(
        user_img if i == 0 else wally_img, 
        encounter_img, 
        model_name='ArcFace', 
        detector_backend='opencv', 
      )
    except Exception as e:
      raise e
    
    if not obj["verified"]:
      return False
    
  return True

@app.route('/validate-encounter', methods=['POST'])
def main():
  data = request.json
  types = [data['userId'], data['wallyId'], data['encounterId']]

  try:
    user_img = save_files_locally(types[0])
    wally_img = save_files_locally(types[1])
    encounter_img = save_files_locally(types[2])
  except Exception as e:
    print(e)
    return jsonify({'error': 'Could not find the images'}), 404

  try:
    validate_img = validate(user_img, wally_img, encounter_img)
  except ValueError as e:
    print(e)
    return jsonify({'error': 'No faces found'}), 404

  for t in types:
    path = f'{DOWNLOAD_PATH}/{t}.{IMAGE_FORMATTING}'
    os.remove(path)

  if validate_img:
    return jsonify({'message': 'Perfect match!'}), 200
  else:
    return jsonify({'error': 'The images do not match'}), 400

if __name__ == '__main__':
  app.run(debug=True) 