# SDF File Format Support

## Overview

PharmGPT now supports SDF (Structure Data File) and MOL file formats, commonly used in pharmaceutical and chemical research to store molecular structure information.

## Supported Formats

- `.sdf` - Structure Data File (can contain multiple molecules)
- `.mol` - MOL file (typically single molecule)

## Features

### With RDKit (Recommended)

When `rdkit-pypi` is installed, the system provides advanced molecular parsing:

- **Molecular Formula**: Automatically calculated (e.g., C9H8O4)
- **Molecular Weight**: Precise calculation in g/mol
- **Atom/Bond Counts**: Accurate structural information
- **SMILES Representation**: Simplified molecular-input line-entry system
- **InChI**: International Chemical Identifier
- **Property Extraction**: All metadata fields from the SDF file

### Without RDKit (Fallback)

If RDKit is not available, the system uses a fallback parser that:

- Extracts compound names
- Reads atom and bond counts from the SDF structure
- Parses all property fields (e.g., Name, Formula, CID)
- Handles multi-molecule SDF files

## Installation

### With RDKit (Recommended)

RDKit is included in `requirements.txt` and will be installed automatically:

```bash
pip install -r requirements.txt
```

Or install separately:

```bash
pip install rdkit-pypi
```

**Note**: If you encounter installation issues with `rdkit-pypi`, consider using conda:

```bash
conda install -c conda-forge rdkit
```

### Without RDKit

No additional installation needed. The fallback parser works with standard Python libraries. If RDKit installation fails, the system will automatically use the fallback parser with reduced functionality.

## Usage

Upload SDF or MOL files through the document upload endpoint just like any other document format:

```python
# The system automatically detects .sdf and .mol extensions
# and processes them appropriately
```

## Example Output

### Single Molecule

```
Compound: Aspirin
Molecular Formula: C9H8O4
Molecular Weight: 180.16 g/mol
Number of Atoms: 13
Number of Bonds: 13
SMILES: O=COc1cccc(CC(=O)O)c1

Properties:
  PUBCHEM_COMPOUND_CID: 2244
  PUBCHEM_MOLECULAR_FORMULA: C9H8O4
  PUBCHEM_MOLECULAR_WEIGHT: 180.16
```

### Multi-Molecule SDF

When an SDF file contains multiple molecules, each molecule is processed as a separate document with its own metadata and content.

## Metadata

Each SDF document includes the following metadata:

- `source`: Original filename
- `loader`: "SDFLoader"
- `file_type`: "sdf"
- `compound_name`: Name of the compound
- `molecular_formula`: Chemical formula (if available)
- `molecular_weight`: Weight in g/mol (if available)
- `num_atoms`: Number of atoms
- `num_bonds`: Number of bonds
- `structure_index`: Index in multi-molecule files
- `properties`: Dictionary of all SDF properties

## Testing

Run the standalone SDF tests:

```bash
python backend/tests/test_sdf_standalone.py
```

This tests:
1. RDKit-based parsing (if available)
2. Fallback parsing without RDKit
3. Multi-molecule SDF handling

## Error Handling

The SDF loader includes comprehensive error handling:

- **Invalid SDF Structure**: Returns clear error message
- **Corrupted Files**: Skips invalid molecules and processes valid ones
- **Empty Files**: Returns appropriate error
- **Missing Properties**: Gracefully handles missing data fields

## Performance

- Single molecule files: < 100ms
- Multi-molecule files (100 molecules): < 2 seconds with RDKit
- Fallback parsing is slightly faster but less accurate

## Limitations

- Very large SDF files (>1000 molecules) may take longer to process
- 3D coordinates are read but not currently used for analysis
- Some advanced molecular descriptors require RDKit

## Future Enhancements

Potential improvements for future versions:

- Molecular similarity search
- Structure-based queries
- 3D structure visualization
- Advanced molecular descriptor calculations
- Chemical reaction support
