import re
import os
import concurrent.futures
import json

DatabasePath  = r""     # Your database path (only "desktop/folder" for example)
DatabaseDir   = "false" # Put 'true' if you want to scan every files in the database path.

RESET="\033[0m"

Ros     = "\033[38;2;255;105;180m"
RosCl   = "\033[38;2;255;135;192m"
VioCl   = "\033[38;2;219;112;147m" 
Vio     = "\033[38;2;186;85;211m"  
VioFonc = "\033[38;2;138;43;226m" 

Banner = rf"""

{Ros}               ___                                    
{RosCl}              / _ \ _   _  ___ _ __ ___   ___ _______ 
{VioCl}             | | | | | | |/ _ \ '__/ _ \ / _ \_  / _ \
{Vio}             | |_| | |_| |  __/ | | (_) | (_) / /  __/
{VioFonc}              \__\_\\__,_|\___|_|  \___/ \___/___\___|                                                                                          
{RESET}

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
        print(f'  {Vio}├• {Ros}File: {RosCl}{Filename} {Ros}Line: {Vio}{Line}{RESET}')

        username = Data.get("username", "N/A")
        email = Data.get("email", "N/A")
        ip = Data.get("ip", "N/A")

        print(f'  {Vio}├• {Ros}Username: {RosCl}{username} ({DetectDataType(username)}){RESET}')
        print(f'  {Vio}├• {Ros}Email: {RosCl}{email} ({DetectDataType(email)}){RESET}')
        print(f'  {Vio}├• {Ros}IP: {RosCl}{ip} ({DetectDataType(ip)}){RESET}')

        print(f'  {Vio}├─ Unknown Data ─────────────{RESET}')
        AdditionalFields = {Key: Value for Key, Value in Data.items() if Key not in ["username", "email", "ip", "_id", "uuid", "events"]}
        for Key, Value in AdditionalFields.items():
            print(f'  {Vio}├• {Ros}{Key}: {RosCl}{Value}{RESET}')
        
        print(f"  └\n")

    else:
        print(f'  {Vio}├• {Ros}Raw data: {RosCl}{Data}{RESET}')
        print(f'  {Vio}└\n')

def Querooze():
    print(Banner)

    if DatabaseDir == "false":
        DatabaseInput = input(f" >{Vio}•{RESET}< {RosCl}Enter name of file you want to process (without extension):{RESET} ")
        if not DatabaseInput.endswith('.txt'):
            DatabaseInput += '.txt'


    SearchInput = input(f" >{Vio}•{RESET}< {RosCl}Enter information you want to search for:{RESET} ")

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
                    print(f"  {Vio}└• {Ros}Match found in file: {RosCl}{Filepath} {Ros}on line {Vio}{Num}{RESET}")

                    try:
                        JsonData = json.loads(Line)
                        Matches.append((JsonData, Filename, Num))
                        
                    except json.JSONDecodeError:
                        Parts = [Part.strip() for Part in Line.split(',')]
                        Matches.append((Parts, Filename, Num))

            return Matches

        AllMatches = []

        with concurrent.futures.ThreadPoolExecutor() as Executor:
            for Root, Dirs, Files in os.walk(Path):
                print(f"\n  {Vio}• Search in: {Root}{RESET}")

                if not Files:
                    print(f"  {Vio}└• {Ros}No Data found in {Root}{RESET}")
                else:
                    Futures = [Executor.submit(SearchInFile, os.path.join(Root, File)) for File in Files if File.endswith('.txt')]

                    for Future in concurrent.futures.as_completed(Futures):
                        Result = Future.result()
                        if Result:
                            AllMatches.extend(Result)

                    if not AllMatches:
                        print(f"  {Vio}└• {Ros}No Data found in {Root}{RESET}")

        return AllMatches

    if DatabaseDir.lower() == "true":
        Path = DatabasePath
    else:
        Path = os.path.join(DatabasePath, f'{DatabaseInput}')

    Matches = LookDatabase(Path, SearchInput)

    if Matches:
        for Data, Filename, Line in Matches:
            print(f"\n  {Vio}•────────{RESET} Data Found ({SearchInput}) {Vio}────────•")
            print(f"  {Vio}│")
            PrintData(Data, Filename, Line)

    else:
        print(f"\n  • No data found for {Vio}{SearchInput}{RESET}")

Querooze()
