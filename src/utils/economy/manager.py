import sqlite3

from bot import get_setting

class EconomyManager:
    def check_sufficient_amount(self, userID: str, amount: int) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT balance FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            balance = val[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        cursor.close()
        db.close()
        
        if balance < amount:
            return False

        return True

    def set_money(self, userID: str, amount: int) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        sql = ('UPDATE economy SET balance = ? WHERE user_id = ?')
        val = (amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def set_ticket(self, userID: str, amount: int) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        sql = ('UPDATE economy SET tpass = ? WHERE user_id = ?')
        val = (amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def add_money(self, userID: str, amount: int, updateGain: bool) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT balance, total FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            balance = val[0] # balance SHOULD be at index 0
            total = val[1] # total SHOULD be at index 1
        except:
            balance = 0
            total = 0
        
        sql = ('UPDATE economy SET balance = ?, total = ? WHERE user_id = ?')
        val = (balance + amount, total + amount, userID) if updateGain else (balance + amount, total, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def add_ticket(self, userID: str, amount: int) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT tpass FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            balance = val[0] # balance SHOULD be at index 0
        except:
            balance = 0
        
        sql = ('UPDATE economy SET tpass = ? WHERE user_id = ?')
        val = (balance + amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def remove_money(self, userID: str, amount: int, updateLoss: bool) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT balance, loss FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            balance = val[0] # balance SHOULD be at index 0
            loss = val[1] # loss SHOULD be at index 1
        except:
            balance = 0
            loss = 0
        
        if balance < amount:
            return False
        
        sql = ('UPDATE economy SET balance = ?, loss = ? WHERE user_id = ?')
        val = (balance - amount, loss + amount, userID) if updateLoss else (balance - amount, loss, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def remove_ticket(self, userID: str, amount: int) -> bool:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT tpass FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            tpass = val[0] # balance SHOULD be at index 0
        except:
            tpass = 0
        
        if tpass < amount:
            return False
        
        sql = ('UPDATE economy SET tpass = ? WHERE user_id = ?')
        val = (tpass - amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def add_gain(self, userID: str, amount: int):
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT total FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            gain = val[0] # gain SHOULD be at index 0
        except:
            gain = 0
        
        sql = ('UPDATE economy SET total = ? WHERE user_id = ?')
        val = (gain + amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def remove_gain(self, userID: str, amount: int):
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT total FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            gain = val[0] # gain SHOULD be at index 0
        except:
            gain = 0
        
        sql = ('UPDATE economy SET total = ? WHERE user_id = ?')
        val = (gain - amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def add_loss(self, userID: str, amount: int):
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT loss FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            loss = val[0] # gain SHOULD be at index 0
        except:
            loss = 0
        
        sql = ('UPDATE economy SET loss = ? WHERE user_id = ?')
        val = (loss + amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True

    def remove_loss(self, userID: str, amount: int):
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()
        
        cursor.execute(f'SELECT loss FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
        val = cursor.fetchone() # grabs the values of user's balance
        
        try:
            loss = val[0] # gain SHOULD be at index 0
        except:
            loss = 0
        
        sql = ('UPDATE economy SET loss = ? WHERE user_id = ?')
        val = (loss - amount, userID)
        
        cursor.execute(sql, val) # executes the instructions
        db.commit() # saves changes
        cursor.close()
        db.close()
        
        return True