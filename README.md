# DSC2204-Group7-ITP-Project

## 1. Installation Guide
Enter this code to create a virtual environment, then use pip install to install all the libraries in the `requirements.txt`:

python -m venv venv_env

pip install -r requirements.txt

Next create a folder called 'models' and download these 2 models from huggingface and place it in the models folder
https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/blob/main/mistral-7b-instruct-v0.1.Q5_K_M.gguf
https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/blob/main/mistral-7b-instruct-v0.1.Q3_K_S.gguf


##2.Prompt Template
In the chromaDB, there is a json file called prompt_template.json, the format of it is "question:response"

An example in the json file would be:
{
  "What is a Goods Receiving Note (GRN)?": "A Goods Receiving Note (GRN) is a document used by businesses to confirm the receipt of goods from suppliers. It details the products received, the quantity, and the condition of the goods upon arrival."
}
