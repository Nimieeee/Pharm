"""
Standalone test for SDF parsing logic
Tests the SDF parsing without requiring full app imports
"""
import tempfile
import os


def test_rdkit_sdf_parsing():
    """Test SDF parsing with rdkit"""
    print("Test 1: RDKit SDF Parsing")
    
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
    except ImportError:
        print("   ⚠️  RDKit not available, skipping rdkit test")
        return True
    
    # Create a simple SDF file
    sdf_content = """Aspirin
  -ISIS-  01231512342D

 13 13  0  0  0  0  0  0  0  0999 V2000
    2.8660   -0.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    3.7320   -0.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.7320    0.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    4.5981   -0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    5.4641   -0.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    6.3301   -0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962   -0.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    6.3301    1.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    5.4641    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    6.3301    2.2500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962    2.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962    3.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  2  0  0  0  0
  2  4  1  0  0  0  0
  4  5  1  0  0  0  0
  5  6  2  0  0  0  0
  6  7  1  0  0  0  0
  7  8  2  0  0  0  0
  8  9  1  0  0  0  0
  9 10  2  0  0  0  0
 10  5  1  0  0  0  0
  9 11  1  0  0  0  0
 11 12  1  0  0  0  0
 12 13  2  0  0  0  0
M  END
> <PUBCHEM_COMPOUND_CID>
2244

> <PUBCHEM_MOLECULAR_FORMULA>
C9H8O4

> <PUBCHEM_MOLECULAR_WEIGHT>
180.16

$$$$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdf', delete=False) as tmp:
        tmp.write(sdf_content)
        tmp_path = tmp.name
    
    try:
        # Parse with rdkit
        supplier = Chem.SDMolSupplier(tmp_path, removeHs=False, sanitize=True)
        
        molecules = []
        for mol in supplier:
            if mol is not None:
                molecules.append(mol)
        
        assert len(molecules) > 0, "No molecules parsed"
        
        mol = molecules[0]
        
        # Get molecular properties
        mol_formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
        mol_weight = Descriptors.MolWt(mol)
        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()
        
        print(f"   ✅ Parsed molecule successfully")
        print(f"   ✅ Formula: {mol_formula}")
        print(f"   ✅ Weight: {mol_weight:.2f} g/mol")
        print(f"   ✅ Atoms: {num_atoms}, Bonds: {num_bonds}")
        
        # Get SMILES
        smiles = Chem.MolToSmiles(mol)
        print(f"   ✅ SMILES: {smiles}")
        
        return True
    except Exception as e:
        print(f"   ❌ RDKit parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(tmp_path)


def test_fallback_sdf_parsing():
    """Test SDF parsing without rdkit (fallback)"""
    print("\nTest 2: Fallback SDF Parsing")
    
    # Create a simple SDF file
    sdf_content = """Ethanol
  
  
  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
> <Name>
Ethanol

> <Formula>
C2H6O

$$$$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdf', delete=False) as tmp:
        tmp.write(sdf_content)
        tmp_path = tmp.name
    
    try:
        # Parse manually
        with open(tmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by molecule delimiter
        molecules = content.split('$$$$')
        molecules = [m.strip() for m in molecules if m.strip()]
        
        assert len(molecules) > 0, "No molecules found"
        
        mol_block = molecules[0]
        lines = mol_block.split('\n')
        
        # First line is compound name
        compound_name = lines[0].strip()
        assert compound_name == 'Ethanol', f"Wrong compound name: {compound_name}"
        
        # Extract properties
        properties = {}
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('>'):
                prop_name = line.strip('<> ')
                if i + 1 < len(lines):
                    prop_value = lines[i + 1].strip()
                    properties[prop_name] = prop_value
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        assert 'Name' in properties, "Name property not found"
        assert properties['Name'] == 'Ethanol', "Wrong name in properties"
        
        # Extract atom/bond counts from line 4
        counts_line = lines[3].strip()
        parts = counts_line.split()
        num_atoms = int(parts[0])
        num_bonds = int(parts[1])
        
        assert num_atoms == 3, f"Wrong atom count: {num_atoms}"
        assert num_bonds == 2, f"Wrong bond count: {num_bonds}"
        
        print(f"   ✅ Parsed molecule successfully")
        print(f"   ✅ Compound: {compound_name}")
        print(f"   ✅ Atoms: {num_atoms}, Bonds: {num_bonds}")
        print(f"   ✅ Properties: {properties}")
        
        return True
    except Exception as e:
        print(f"   ❌ Fallback parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(tmp_path)


def test_multi_molecule_parsing():
    """Test parsing multiple molecules from one SDF"""
    print("\nTest 3: Multi-Molecule SDF")
    
    sdf_content = """Molecule1
  
  
  2  1  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
M  END
$$$$
Molecule2
  
  
  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
$$$$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdf', delete=False) as tmp:
        tmp.write(sdf_content)
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        molecules = content.split('$$$$')
        molecules = [m.strip() for m in molecules if m.strip()]
        
        assert len(molecules) == 2, f"Expected 2 molecules, got {len(molecules)}"
        
        # Check first molecule
        lines1 = molecules[0].split('\n')
        assert lines1[0].strip() == 'Molecule1', "Wrong first molecule name"
        
        # Check second molecule
        lines2 = molecules[1].split('\n')
        assert lines2[0].strip() == 'Molecule2', "Wrong second molecule name"
        
        print(f"   ✅ Parsed {len(molecules)} molecules")
        print(f"   ✅ Molecule 1: {lines1[0].strip()}")
        print(f"   ✅ Molecule 2: {lines2[0].strip()}")
        
        return True
    except Exception as e:
        print(f"   ❌ Multi-molecule parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(tmp_path)


def main():
    """Run all tests"""
    print("="*60)
    print("Testing SDF Parsing Logic")
    print("="*60)
    print()
    
    results = []
    
    results.append(test_rdkit_sdf_parsing())
    results.append(test_fallback_sdf_parsing())
    results.append(test_multi_molecule_parsing())
    
    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All SDF parsing tests passed!")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    print("="*60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
