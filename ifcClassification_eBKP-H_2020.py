# Converts a classification as csv into an IfcClassication.
# Output is an ifc file to be used in Bonsai BIM as a classication reference file.
# Extracts the hierachy and creates the same in ifc.
# Input csv only has 2 columns for code and name, without header.

import pandas as pd
import ifcopenshell

try:
    # Load the data again as previous attempts failed, this time without header
    df_ebkp_h = pd.read_csv('IfcClassification_eBKP-H_2020.csv', header=None)

    # Rename columns to 'Code' and 'Description'
    df_ebkp_h = df_ebkp_h.rename(columns={0: 'Code', 1: 'Description'})

    # Ensure 'Code' is treated as string
    df_ebkp_h['Code'] = df_ebkp_h['Code'].astype(str)

    # Determine the level based on code length
    df_ebkp_h['level'] = df_ebkp_h['Code'].str.len()

    # Define a function to get the parent code based on the new hierarchy
    def get_parent_code(row):
        code = row['Code']
        level = row['level']
        if level == 1:
            return None
        elif level == 3:
            return code[0] # Parent is the first character
        elif level == 6:
            return code[:3] # Parent is the first three characters
        else:
            return None

    # Apply the function to create the 'parent_code' column
    df_ebkp_h['parent_code'] = df_ebkp_h.apply(get_parent_code, axis=1)

    # Display head and info to verify processing
    display(df_ebkp_h.head())
    display(df_ebkp_h.info())

    # Now proceed with the Generator code since the DataFrame is loaded and processed
    class Generator():
        def __init__(self):
            self.file = ifcopenshell.file(schema='IFC4')
            self.out_dir = './'
            self.references = {} # Dictionary to store created references by code

        def generate(self, df):
            classification = self.file.create_entity('IfcClassification', **{
                'Source': 'CRB',
                'Edition': '2020',
                'EditionDate': '2020-09-28',
                'Name': 'eBKP-H',
                'Description': 'Elementbasierter Baukostenplan Hochbau Schweiz',
                'ReferenceTokens': ['eBKP-H']
            })

            self.references[None] = classification # Map None parent to the main classification

            # Sort DataFrame alphabetically by Code
            df_sorted = df.sort_values(by='Code')

            for index, row in df_sorted.iterrows():
                code = str(row['Code'])
                name = row['Description']
                parent_code = row['parent_code']

                ref = self.file.create_entity('IfcClassificationReference', **{
                    'Identification': code,
                    'Name': name
                })

                self.references[code] = ref

                # Establish hierarchy
                if parent_code in self.references:
                    ref.ReferencedSource = self.references[parent_code]
                else:
                    # This should not happen if sorted correctly and data is consistent
                    print(f"Warning: Parent code {parent_code} not found for code {code}")
                    # As a fallback, link to the main classification if parent is missing
                    ref.ReferencedSource = classification


            self.file.write('IfcClassification_eBKP-H_2020.ifc')

    # Instantiate the generator and call generate with the DataFrame
    generator = Generator()
    generator.generate(df_ebkp_h)

except FileNotFoundError:
    print("Error: 'IfcClassification_eBKP-H_2020.csv' not found. Please ensure the file is in the correct directory.")
    df_ebkp_h = None # Set df_ebkp_h to None to indicate failure
except KeyError as e:
    print(f"Error: Column {e} not found. Please check the column names in your CSV file.")
    df_ebkp_h = None # Set df_ebkp_h to None to indicate failure
