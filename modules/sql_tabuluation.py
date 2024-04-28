import sqlite3
from sqlite3 import Error
class sqltime():
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file)
            print(f"Connected to SQLite database file '{db_file}'")
        except Error as e:
            print(e)
    def close_connection(self):
        if self.conn:
            self.conn.close()
            print("Connection to SQLite database closed")
    def create_tables(self):
        
        c = "CREATE TABLE IF NOT EXISTS my_table (\n"
        for i in range(1,190):
            c = c + "col"+str(i)+ ",\n"
        c = c.strip().strip(",")+");"
        #print(c)
        self.conn.cursor().execute(c)
        self.conn.commit()
    #helper function to convert output to a list to be read into a sql row
    def make_list(self,d,ticker):
        lst=[ticker]
        for d in d[ticker].values():
            for num in d.values():
                try:
                    for x in num.values():
                        try:
                            for i in x.values():
                                try:
                                    for a in i.values():
                                        lst.append(a)
                                except:
                                    lst.append(i)

                        except:
                            lst.append(x)
                except:
                    lst.append(num)
        return(lst)
    #insert data into database, CHECK CACHE FIRST!!!
    def insert_data(self, data, ticker):
        l = self.make_list({ticker:data}, ticker)
        print(l)
        #insert_query = f"INSERT INTO my_table VALUES ({', '.join(['?']*189)})"
        insert_query = f"INSERT INTO my_table VALUES ({', '.join(['?'] * 189)})"
        # Execute the SQL query
        self.conn.cursor().execute(insert_query, l)
        
        # Commit the transaction
        self.conn.commit()
    #asks if ticker is in database
    def check_cache(self, ticker):
        check_query = "SELECT COUNT(*) FROM my_table WHERE col1 = ?"
        # Execute the SQL query
        self.cursor().execute(check_query, (ticker,))
        result = self.cursor().fetchone()[0]
        if result > 0:
            return True
        else:
            return False
    def retrieve_valuation(self, ticker):
                cursor = self.conn.cursor()
                check_query = "SELECT * FROM my_table WHERE col1 = ?"
                cursor.execute(check_query, (ticker,))
                first_row = cursor.fetchone()

                if first_row:
                    # Extract all attributes from the first row
                    a = list(first_row)
                    a.pop(0)
                    valuation_output = {
            'projection_table': {
                'base_year': {
                    'Revenue' : a[0],
                    'Operating Margin' : a[1],
                    'Operating Income' : a[2],
                    'Tax Rate' : a[3],
                    'NOPAT' : a[4], # NOPAT = Operating Income * (1 - Tax Rate)
                    'NOL' : a[5],
                },
                'future_years': {
                    f'Year {year + 1}': {
                        'Revenue Growth Rate' : a[12*(year)+6],
                        'Revenue': a[12*(year)+7],
                        'Operating Margin': a[12*(year)+8],
                        'Operating Income': a[12*(year)+9],
                        'Tax Rate': a[12*(year)+10],
                        'NOPAT': a[12*(year)+11],
                        'Reinvestment': a[12*(year)+12],
                        'FCFF': a[12*(year)+13],
                        'NOL': a[12*(year)+14],
                        'Cost of Capital': a[12*(year)+15],
                        'Cumulated Discount Factor': a[12*(year)+16],
                        'PV(FCFF)': a[12*(year)+17],
                    } for year in range(10)
                },
                'terminal_year': {
                    'Revenue Growth Rate' : a[125],
                    'Revenue' : a[126],
                    'Operating Margin' : a[127],
                    'Operating Income' : a[128],
                    'Tax Rate' : a[129],
                    'NOPAT' : a[130], # NOPAT = Operating Income * (1 - Tax Rate)
                    'Reinvestment' : a[131],
                    'FCFF' : a[132],
                    'NOL' : a[133],
                    'Cost of Capital' : a[134],
                },
            },
            'summary_table' : {
                'Terminal Cash Flow' : a[135],
                'Terminal Cost of Capital' : a[136],
                'Terminal Value' : a[137],
                'PV(Terminal Value)' : a[138],
                'PV(CF over next 10 years)' : a[139],
                'Sum of PV' : a[140],
                'Probability of Failure' : a[141],
                'Proceeds if Firm Fails' : a[142],
                'Value of Operating Assets' : a[143],
                'Debt' : a[144],
                'Minority Interests' : a[145],
                'Cash' : a[146],
                'Non-Operating Assets' : a[147],
                'Value of Equity' : a[148],
                'Value of Options' : a[149],
                'Value of Equity in Common Stock' : a[150],
                'Estimated Value / Share' : a[151],
                'Price per Share' : a[152],
                'Price as % of Value' : a[153],
            },
            'implied_variables_table': {
                'base_year' : {
                    'Invested Capital' : a[154],
                    'Return on Invested Capital' : a[155],
                },
                'future_years': {
                    f'Year {year + 1}' : {
                        'Sales to Capital Ratio': a[3*(year)+156],
                        'Invested Capital': a[3*(year)+156],
                        'Return on Invested Capital': a[3*(year)+156],
                    } for year in range(10)
                },
                'terminal_year' : {
                    'Return on Invested Capital' : 187,
                },
            },
        }
                    return valuation_output
                else:
                    print("No rows found.")

                
        
    def print_db(self):
        cursor = self.conn.cursor()

        # Execute a SELECT query to fetch data from a specific table
        cursor.execute("SELECT * FROM my_table")  # Replace 'your_table' with the name of your table

        # Fetch all rows from the cursor
        rows = cursor.fetchall()

        # Print the contents of the table
        for row in rows:
            print(row)


"""sample usage
output=valuation("F").get_valuation()
print("output", output)
s = sqltime("database.db")
s.create_tables()
s.insert_data(output, "F")
s.print_db()
print("Above is database")
print(s.retrieve_valuation("F"))
s.close_connection()
"""
