import torch
import transformers
from transformers import BertModel, BertTokenizer, BertForSequenceClassification
from transformers import pipeline, Trainer, TrainingArguments

print(torch.cuda.is_available())
device = 0 if torch.cuda.is_available() else -1





train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)

model = BertForSequenceClassification.from_pretrained('bert-base-uncased')

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

classifier = pipeline('text-classification', model='bert-base-uncased', device=device)

result = classifier("I love using Hugging Face models for NLP tasks!")
print(result)
