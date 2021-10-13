# a1-diningconcierge

_Yankai Li (yl4632)_  
_Tarcy Li (ml4683)_
  

This implementation is a serverless, microservice-driven web application. Specifically, a Dining Concierge chatbot that sends the user restaurant suggestions given a set of preferences that the user provides to the chatbot through conversation.

## To Run
Open the url in a browser: https://a1diningconcierge.s3.amazonaws.com/chat.html
  
## Architecture Diagram
![diagram](img/ArchitectureDiagram.png)
  
## Chatbot Screenshot
![diagram](img/ChatbotExample.png)
  
## Used Services
- AWS S3 bucket - host the front-end
- API Gateway - setup API/Swagger
- Amazon Lex - build Dining Concierge chatbot
- SQS - queue user appointment requests
- SNS - send messages/emails
- ElasticSearch - store restaurant ID and Cuisine from Yelp
- DynamoDB - store restaurant information (Business ID, Name, Address, Coordinates, Number of Reviews, Rating, Zip Code) from Yelp
