import torch
from datasets import load_dataset
from transformers import (
    RobertaTokenizerFast,
    RobertaForSequenceClassification,
    TrainingArguments,
    Trainer,
    AutoConfig,
)
import pandas as pd
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
# Torch dataset
class CSRDDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings=encodings
        self.labels=labels
    
    def __getitem__(self, idx):
        item= {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item
    
    def __len__(self):
        return len(self.labels)
# Train and validation sets
def train_val_dataset(train_df):
    train_text, val_text, train_labels, val_labels= train_test_split(train_df.text,train_df.label,test_size=0.2)
    train_text=train_text.reset_index(drop=True)
    val_text=val_text.reset_index(drop=True)
    train_labels=train_labels.reset_index(drop=True)
    val_labels=val_labels.reset_index(drop=True)
    train_encodings= tokenizer(train_text.tolist(), truncation=True, padding=True)
    val_encodings= tokenizer(val_text.tolist(), truncation=True, padding=True)
    train_dataset= CSRDDataset(train_encodings, train_labels)
    val_dataset= CSRDDataset(val_encodings, val_labels)
    return train_dataset, val_dataset
# Traning arguments
def training_arguments(checkpoint_directory):
    training_args = TrainingArguments(
    output_dir=checkpoint_directory,
    num_train_epochs=4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    evaluation_strategy="epoch",
    logging_dir=f"{checkpoint_directory}/logs",
    logging_strategy="steps",
    logging_steps=10,
    learning_rate=5e-5,
    weight_decay=0.01,
    warmup_steps=500,
    save_strategy="epoch",
    load_best_model_at_end=True,
    save_total_limit=2,
    report_to="tensorboard",

)
    return training_args 
#Load model
model_name="roberta-base"
tokenizer = RobertaTokenizerFast.from_pretrained(model_name)
model= RobertaForSequenceClassification.from_pretrained(model_name)
# number of labels 10 (11 if 0 label present in traning dataset)
num_labels=10
class_names=[0,1,2,3,4,5,6,7,8,9]
# configuration
config = AutoConfig.from_pretrained(model_name)
id2label = {i: label for i, label in enumerate(class_names)}
config = AutoConfig.from_pretrained(model_name)
config.update({"id2label": id2label})
# load model with configuration
model = RobertaForSequenceClassification.from_pretrained(model_name, config=config)
# function that fine tunes RoBERTa
def fine_tune_RoBERTa(train_df,checkpoint_directory,save_directory):
    train_dataset, val_dataset=train_val_dataset(train_df)
    training_arg=training_arguments(checkpoint_directory)
    trainer= Trainer(
        model=model,
        args=training_arg,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )
    trainer.train()
    tokenizer.save_pretrained(save_directory)
    model.save_pretrained(save_directory)


