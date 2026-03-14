from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

def test_smiles(name, smiles):
    print(f"Testing {name}: {smiles}")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        print(f"  FAILED: MolFromSmiles returned None")
        return False
    
    try:
        drawer = rdMolDraw2D.MolDraw2DSVG(400, 300)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        print(f"  SUCCESS: Generated SVG ({len(svg)} bytes)")
        return True
    except Exception as e:
        print(f"  FAILED: SVG generation error: {e}")
        return False

smiles_list = [
    ("Lamotrigine", "Nc1nc(N)c2c(Cl)c(Cl)cccc2n1"),
    ("Morphine", "CN1CCC23C4C1CC5=C6C2(CCC5O)OC7=C6C(=CC=C7O)C43"),
    ("Methane", "C"),
    ("Ring%10", "C123456789%10CCCCCCCCC123456789%10") # Example with %
]

for name, smiles in smiles_list:
    test_smiles(name, smiles)
