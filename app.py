from flask import Flask, jsonify, request
from deepface import DeepFace
import os
import supabase

app = Flask(__name__)

DOWNLOAD_PATH = 'download'
IMAGE_FORMATTING = 'jpg'

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def save_files_locally(target: str) -> str:
  client = supabase.create_client(os.getenv('BUCKET_URL'), os.getenv('BUCKET_KEY'))

  response = client.storage.from_(os.getenv('BUCKET_STORAGE')).download(f'{target}.jpg')
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
    except ValueError as e:
      raise ValueError(f"There was a problem trying to compare the images! Image error: {e}")
    if not obj["verified"]:
      return False
    
  return True

@app.route('/validate-encounter', methods=['POST'])
def main():

  data = request.json
  types = [data['user_id'], data['wally_id'], data['encounter_id']]

  user_img = save_files_locally(types[0])
  wally_img = save_files_locally(types[1])
  encounter_img = save_files_locally(types[2])

  try:
    validate_img = validate(user_img, wally_img, encounter_img)
    if validate_img:
      return jsonify({'message': 'Perfect match!'}), 200
    else:
      return jsonify({'error': 'The images do not match'}), 400
  except ValueError as e:
    return jsonify({'error': str(e)}), 404
  finally:
    for t in types:
      path = f'{DOWNLOAD_PATH}/{t}.{IMAGE_FORMATTING}'
      os.remove(path)

if __name__ == '__main__':
  app.run(debug=True) 