from db import queries as Q


class AnalysisRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_sales_analysis(self, date_from_str, date_to_str):
        c = self.conn.cursor()
        c.execute(Q.SALES_ANALYSIS, (date_from_str, date_to_str))
        return c.fetchall()
