import re
import os
import concurrent.futures
import json

DatabasePath = r""    # Your database path
DatabaseDir = "true"  # Put 'false' if you want to scan just one file in the database path.

Reset = "\033[0m"

Ros = "\033[38;2;255;105;180m"
RosCl = "\033[38;2;255;135;192m"
VioCl = "\033[38;2;219;112;147m"
Vio = "\033[38;2;186;85;211m"
VioFonc = "\033[38;2;138;43;226m"

Banner = rf"""
{Ros}               ___                                    
{RosCl}              / _ \ _   _  ___ _ __ ___   ___ _______ 
{VioCl}             | | | | | | |/ _ \ '__/ _ \ / _ \_  / _ \
{Vio}             | |_| | |_| |  __/ | | (_) | (_) / /  __/
{VioFonc}              \__\_\\__,_|\___|_|  \___/ \___/___\___|                                                                                          
{Reset}
"""

def DetectDataType(Data):
    if re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', Data):                      # Verif if data => IP
        return "IP"
    elif re.match(r'^[\w.-]+@[\w.-]+$', Data):                            # Verif if data => EMAIL
        return "Email"
    elif len(Data) > 0 and (Data[0].isalpha() or Data[0] in ["_", "-"]):  # Verif if data => USERNAME/PSEUDO
        return "Username"
    else:
        return "Text"

def PrintData(Data, Filename, Line):
    if isinstance(Data, dict):
        print(f'  {Vio}├• {Ros}File: {RosCl}{Filename} {Ros}Line: {Vio}{Line}{Reset}')

        Username = Data.get("username", "N/A")
        Email = Data.get("email", "N/A")
        IP = Data.get("ip", "N/A")

        print(f'  {Vio}├• {Ros}Username: {RosCl}{Username} ({DetectDataType(Username)}){Reset}')
        print(f'  {Vio}├• {Ros}Email: {RosCl}{Email} ({DetectDataType(Email)}){Reset}')
        print(f'  {Vio}├• {Ros}IP: {RosCl}{IP} ({DetectDataType(IP)}){Reset}')
        print(f'  {Vio}│')
        print(f'  {Vio}├─ Unknown Data Type ─────────────{Reset}')
        print(f'  {Vio}│')
        AdditionalFields = {Key: Value for Key, Value in Data.items() if Key not in ["username", "email", "ip", "_id", "uuid", "events"]}
        for Key, Value in AdditionalFields.items():
            print(f'  {Vio}├• {Ros}{Key}: {RosCl}{Value}{Reset}')

        print(f"  └\n")

    else:
        
        RawUsername = "N/A"
        RawEmail = "N/A"
        RawIP = "N/A"
        UnknownData = []

        for Part in Data:
            if DetectDataType(Part) == "Username":
                RawUsername = Part
            elif DetectDataType(Part) == "Email":
                RawEmail = Part
            elif DetectDataType(Part) == "IP":
                RawIP = Part
            else:
                UnknownData.append(Part)

        print(f'  {Vio}├• {Ros}Username: {RosCl}{RawUsername}{Reset}')
        print(f'  {Vio}├• {Ros}Email: {RosCl}{RawEmail}{Reset}')
        print(f'  {Vio}├• {Ros}IP: {RosCl}{RawIP}{Reset}')

        if UnknownData:
            print(f'  {Vio}│')
            print(f'  {Vio}├─ Unknown Data Type ─────────────{Reset}')
            print(f'  {Vio}│')
            for Value in UnknownData:
                print(f'  {Vio}├• {Ros}DATA: {Ros}{Value}{Reset}')
        
        print(f'  {Vio}│')
        print(f'  {Vio}├─ Raw Data ─────────────{Reset}')
        print(f'  {Vio}│')
        print(f'  {Vio}├• {Ros}DATA: {RosCl}{Data}{Reset}')
        
        print(f'  {Vio}└\n')

def Querooze():
    print(Banner)

    if DatabaseDir.lower() == "false":
        DatabaseInput = input(f" >{Vio}•{Reset}< {RosCl}Enter name of file you want to process (without extension):{Reset} ")
        if not DatabaseInput.endswith('.txt'):
            DatabaseInput += '.txt'

    SearchInput = input(f" >{Vio}•{Reset}< {RosCl}Enter information you want to search for:{Reset} ")

    def LookDatabase(Path, SearchInput):
        UserPattern = re.compile(rf'{re.escape(SearchInput)}', re.IGNORECASE)

        def SearchInFile(Filepath):
            Filename = os.path.basename(Filepath)

            try:
                with open(Filepath, 'r', errors='ignore') as PlainFile:
                    Lines = PlainFile.readlines()

            except Exception as e:
                return []

            Matches = []
            for Num, Line in enumerate(Lines, 1):
                if UserPattern.search(Line):
                    print(f"  {Vio}└• {Ros}Match found in file: {RosCl}{Filepath} {Ros}on line {Vio}{Num}{Reset}")

                    try:
                        JsonData = json.loads(Line)
                        Matches.append((JsonData, Filename, Num))

                    except json.JSONDecodeError:
                        Parts = [Part.strip() for Part in Line.split(',')]
                        Matches.append((Parts, Filename, Num))

            return Matches

        AllMatches = []

        if DatabaseDir.lower() == "true":
            with concurrent.futures.ThreadPoolExecutor() as Executor:
                for Root, Dirs, Files in os.walk(Path):
                    print(f"\n  {Vio}• Search in: {Root}{Reset}")

                    if not Files:
                        print(f"  {Vio}└• {Ros}No Data found in {Root}{Reset}")

                    else:
                        Futures = [Executor.submit(SearchInFile, os.path.join(Root, File)) for File in Files]
                        for Future in concurrent.futures.as_completed(Futures):
                            Result = Future.result()
                            if Result:
                                AllMatches.extend(Result)

                        if not AllMatches:
                            print(f"  {Vio}└• {Ros}No Data found in {Root}{Reset}")
        else:
            print(f"\n  {Vio}• Search in: {DatabaseInput}{Reset}")

            SingleFilePath = os.path.join(Path)
            Matches = SearchInFile(SingleFilePath)
            if Matches:
                AllMatches.extend(Matches)

        return AllMatches

    if DatabaseDir.lower() == "true":
        Path = DatabasePath

    else:
        Path = os.path.join(DatabasePath, DatabaseInput)

    Matches = LookDatabase(Path, SearchInput)

    if Matches:
        for Data, Filename, Line in Matches:
            print(f"\n  {Vio}┌────────{Reset} Data Found ({SearchInput}) {Vio}────────•")
            print(f"  {Vio}│")
            PrintData(Data, Filename, Line)
    else:
        print(f"\n  • No data found for {Vio}{SearchInput}{Reset}")



while True:
    Querooze()

    if input("\n   Want to continue ? (y/n): ") == "y":
        os.system("cls" if os.name == "nt" else "clear")
        continue
    
    else:
        break
