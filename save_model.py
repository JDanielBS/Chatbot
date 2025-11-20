from sentence_transformers import SentenceTransformer

model_id = "intfloat/multilingual-e5-large"

local_path = "models/multilingual-e5-large"
model = SentenceTransformer(model_id)
model.save(local_path)
