from sentiment import company_sentiment

def main():
    company_name = input("Enter a company name: ")
    sentiment = company_sentiment(company_name)
    print(sentiment)

if __name__ == "__main__":
    main()