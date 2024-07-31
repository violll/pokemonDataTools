import openpyxl
import openpyxl.formatting
import openpyxl.styles
import pandas as pd

class NRotMEncounterRouting():
    def __init__(self) -> None:
        self.wb = openpyxl.load_workbook(filename = "EncounterRoutingNRotM/NRotM August 2024 - Platinum Healless Typeban v1.0.xlsx")
        self.ws = self.wb["Team & Encounters"]

        # SPECIFIC TO THIS SHEET
        self.relevantCol = "J"
        self.encounters = self.ws["J5:J64"]

        self.encounterData = self.getEncounterData()
        self.encounterTable = self.getEncounterTable()

    def getEncounterData(self):
        res = []

        dvList = self.ws.data_validations.dataValidation
        for dv in dvList: 
            cells = [str(c) for c in list(dv.sqref.ranges) if self.relevantCol in str(c)]   # a list of CellRange elements
            
            if cells == []: continue 

            encounters = dv.formula1.replace('"', "").split(",")                            # a list of encounters

            cells = self.expandColon(cells)
            for c in cells: 
                loc = c.replace(self.relevantCol, chr(ord(self.relevantCol)-1))
                route = self.ws[loc].value
                # print("{} are available at {}".format(", ".join(encounters), route))
                res.extend([route, enc, 1] for enc in encounters)

        return res

    def expandColon(self, cells):
        res = []
        for cell in cells:
            if ":" not in cell: res.append(cell)
            else:
                start, stop = map(int, cell.replace(self.relevantCol, "").split(":"))
                while start <= stop:
                    res.append(self.relevantCol + str(start))
                    start += 1

        return res

    def getEncounterTable(self):
        df = pd.DataFrame.from_records(self.encounterData, columns=["Route", "Encounter", "Value"]) \
                         .pivot(index="Route", columns="Encounter", values="Value").fillna(0)

        # REMOVE HASHES FROM COLORS TO MAKE THEM USABLE
        greenFill = openpyxl.styles.PatternFill(bgColor='c6efce', fill_type='solid')
        greenFont = openpyxl.styles.Font(color="006100")

        with pd.ExcelWriter("EncounterRoutingNRotM/test.xlsx") as writer:
            df.to_excel(writer, sheet_name="EncounterTable", freeze_panes=(1, 1))

            workbook = writer.book
            worksheet = writer.sheets["EncounterTable"]

            (max_row, max_col) = df.shape

            # fills the background color
            worksheet.conditional_formatting.add("B2:BN56", openpyxl.formatting.rule.CellIsRule(operator='equal', formula=[1], stopIfTrue=False, fill=greenFill, font=greenFont))
            # worksheet.alignment = openpyxl.styles.alignment.Alignment(horizontal="center") TODO align all rows
            # worksheet.column_dimensions["A"].bestFit = True TODO autofit the column lenghths https://stackoverflow.com/questions/13197574/openpyxl-adjust-column-width-size

        return df

if __name__ == "__main__":
    NRotMEncounterRouting()