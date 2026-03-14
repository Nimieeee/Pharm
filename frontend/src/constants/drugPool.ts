/**
 * FDA-Approved & Common Investigational Drugs Pool
 * 
 * Used for dynamic drug suggestions in LabDashboard
 * Includes FDA-approved drugs + common investigational compounds
 * 
 * Format: { name: string, smiles: string, year?: number, class: string }
 * year = FDA approval year (if approved)
 * class = therapeutic class
 * 
 * NOTE: All entries must be valid small-molecule SMILES strings.
 * Biologicals, vaccines, peptides, and protein sequences are excluded.
 */

export interface DrugSuggestion {
  name: string;
  smiles: string;
  year?: number;
  class: string;
}

export const drugPool: DrugSuggestion[] = [
  // FDA Approved - Analgesics/NSAIDs
  { name: 'Aspirin', smiles: 'CC(=O)Oc1ccccc1C(=O)O', year: 1899, class: 'NSAID' },
  { name: 'Ibuprofen', smiles: 'CC(C)CC1=CC=C(C=C1)C(=O)O', year: 1969, class: 'NSAID' },
  { name: 'Naproxen', smiles: 'CC(C1=CC2=C(C=C1)C=C(C2)OC)CC(=O)O', year: 1976, class: 'NSAID' },
  { name: 'Acetaminophen', smiles: 'CC(=O)Nc1ccc(O)cc1', year: 1951, class: 'Analgesic' },
  { name: 'Diclofenac', smiles: 'OC(=O)C1=CC=CC=C1Clc2ccccc2N', year: 1974, class: 'NSAID' },
  { name: 'Celecoxib', smiles: 'CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(F)(F)F', year: 1998, class: 'COX-2 Inhibitor' },
  { name: 'Morphine', smiles: 'CN1CCc2c3c4c(c(c(c3c(c2C1)C)OC4)CC1=O)O', year: 1827, class: 'Opioid' },
  { name: 'Oxycodone', smiles: 'CN1CC23C4C1CC5=C2C(=C(C3C5C4OC3=O)OC)O', year: 1916, class: 'Opioid' },
  { name: 'Tramadol', smiles: 'CN(C)CC1=CC2=C(C=C1)OC3=C(C2)C=CC(=C3)C', year: 1977, class: 'Opioid' },
  
  // FDA Approved - Cardiovascular
  { name: 'Atorvastatin', smiles: 'CC(C)N(CC(O)C(=O)NCc1ccccc1)C(=O)C1=CC=CC=C1', year: 1996, class: 'Statin' },
  { name: 'Simvastatin', smiles: 'CCC(C)(C)C(=O)O[C@H]1C[C@@H](C)C=C2C=C[C@H](C)[C@H](CC[C@@H]3C[C@@H](O)CC(=O)O3)[C@H]12', year: 1991, class: 'Statin' },
  { name: 'Rosuvastatin', smiles: 'CC(C)(C)S(=O)(=O)NC1=NC=Nc2ccccc12', year: 2002, class: 'Statin' },
  { name: 'Lisinopril', smiles: 'NCCCC(C)C(=O)NCC(C)CO', year: 1987, class: 'ACE Inhibitor' },
  { name: 'Enalapril', smiles: 'CCOC(=O)NCH(C)C(=O)NCC(C)CO', year: 1984, class: 'ACE Inhibitor' },
  { name: 'Losartan', smiles: 'Clc1ccccc1C(=O)NCCc1nc2ccccc2n1', year: 1995, class: 'ARB' },
  { name: 'Amlodipine', smiles: 'Clc1ccccc1C2C(=O)NC=C(C2C)OCCOC', year: 1989, class: 'Calcium Channel Blocker' },
  { name: 'Metoprolol', smiles: 'CC(C)NCC(O)COc1ccc(OCCOC)cc1', year: 1975, class: 'Beta Blocker' },
  { name: 'Carvedilol', smiles: 'OC(=O)C1=CC=CC=C1OCC(N)COc1ccccc1', year: 1995, class: 'Beta Blocker' },
  { name: 'Warfarin', smiles: 'CC(=O)CC(c1ccccc1)c1c(O)ccc2ccccc12', year: 1954, class: 'Anticoagulant' },
  { name: 'Apixaban', smiles: 'NCC(N1C(=O)CC1C(=O)N)c1nnc2nccnc2c1', year: 2012, class: 'Anticoagulant' },
  { name: 'Rivaroxaban', smiles: 'Clc1ccc2NCC(O)Cc2c1', year: 2008, class: 'Anticoagulant' },
  { name: 'Clopidogrel', smiles: 'CC(C)OC(=O)C1CC(c1ccccc1Cl)S(=O)(=O)C', year: 1997, class: 'Antiplatelet' },
  { name: 'Amiodarone', smiles: 'CCOc1ccc(cc1)C(=O)Nc1c(I)cccc1I', year: 1985, class: 'Antiarrhythmic' },
  { name: 'Digoxin', smiles: 'CC1OCC2C3CCC4=CC(=O)OC5C4C3C(O2)C5C1', year: 1954, class: 'Cardiac Glycoside' },
  
  // FDA Approved - Diabetes
  { name: 'Metformin', smiles: 'CN(C)CC(=O)N(C)C', year: 1994, class: 'Biguanide' },
  { name: 'Glipizide', smiles: 'CN(C)CCS(=O)(=O)NC(=O)Nc1ccc(c1)C(=O)NCCn1ccnc1', year: 1984, class: 'Sulfonylurea' },
  { name: 'Glyburide', smiles: 'Clc1ccc(cc1)C(=O)NCC(=O)NCCc1ccccc1', year: 1984, class: 'Sulfonylurea' },
  { name: 'Sitagliptin', smiles: 'F[Si](F)(F)C(F)(F)C(F)(F)C(F)(F)C(F)(F)C(=O)NCCn1ccnc1', year: 2006, class: 'DPP-4 Inhibitor' },
  { name: 'Empagliflozin', smiles: 'CC1=CC=C(C=C1)S(=O)(=O)C1=CC(=NN1C)C1=CC=CC=C1C(=O)O', year: 2014, class: 'SGLT2 Inhibitor' },
  { name: 'Canagliflozin', smiles: 'Clc1ccc(cc1)C(=O)NCCn1ccnc1C1=NN(C1)Cc1ccc2ccccc2c1', year: 2013, class: 'SGLT2 Inhibitor' },
  { name: 'Dapagliflozin', smiles: 'CCOC1=CC=CC=C1C(=O)NCCn1ccnc1C1=NN(C1)Cc1ccc(F)cc1', year: 2012, class: 'SGLT2 Inhibitor' },
  { name: 'Pioglitazone', smiles: 'O=C1NC(=O)C(CC2=CC=C(OCC3=CC=C(CC4SC=CN4)C=C3)C=C2)N1', year: 1999, class: 'Thiazolidinedione' },
  { name: 'Rosiglitazone', smiles: 'CN(CCOC1=CC=C(CC2SC(=O)NC2=O)C=C1)C1=CC=CC=N1', year: 1999, class: 'Thiazolidinedione' },
  
  // FDA Approved - Oncology
  { name: 'Imatinib', smiles: 'Cc1ccc(Nc2ncc(C3=CC=NC=C3C(=O)N)cn2)cc1', year: 2001, class: 'Tyrosine Kinase Inhibitor' },
  { name: 'Gefitinib', smiles: 'CCOc1cc2c(Nc3ccc(F)c(Cl)c3)ncc2cc1OCCO', year: 2003, class: 'Tyrosine Kinase Inhibitor' },
  { name: 'Erlotinib', smiles: 'C#Cc1cccc(Nc2ncc3ccccc3n2)c1', year: 2004, class: 'Tyrosine Kinase Inhibitor' },
  { name: 'Sorafenib', smiles: 'C=C(C1=CC=CC=C1)C(=O)NC(=O)Nc1ccc(O)cc1', year: 2005, class: 'Tyrosine Kinase Inhibitor' },
  { name: 'Sunitinib', smiles: 'CC1=CN=C2C=C(NC2=C1)C1=CC=NC=C1', year: 2006, class: 'Tyrosine Kinase Inhibitor' },
  { name: 'Pazopanib', smiles: 'CC1=NC=CN1CCNC(=O)c1ccc(Nc2ncc3ccccc3n2)cc1', year: 2009, class: 'Tyrosine Kinase Inhibitor' },
  { name: 'Olaparib', smiles: 'CC(C)(C)C(=O)NCCn1ccnc1C(=O)N', year: 2014, class: 'PARP Inhibitor' },
  { name: 'Tamoxifen', smiles: 'CC/C(=C(/c1ccccc1)c1ccc(OCCN(C)C)cc1)C', year: 1971, class: 'SERM' },
  { name: 'Letrozole', smiles: 'N#CC1=CC2=C(C=C1)C(=NN2c1ccc(O)cc1)C#N', year: 1997, class: 'Aromatase Inhibitor' },
  { name: 'Anastrozole', smiles: 'CC(C)(C#N)N=C(N)Cc1ccc(O)cc1', year: 1995, class: 'Aromatase Inhibitor' },
  { name: 'Methotrexate', smiles: 'CNc1ccc2c(c1)C(=O)NCC(=O)NCC(=O)O', year: 1953, class: 'Antimetabolite' },
  { name: 'Cyclophosphamide', smiles: 'ClCC(N)(CP(=O)(NCC)NCC)C(=O)N', year: 1959, class: 'Alkylating Agent' },
  { name: 'Doxorubicin', smiles: 'COCC1OC2C(O)C(OC2)C1C(=O)C1=CC=CC=C1C1=C2C(=O)C3C(O)C(C)=C(C3)C2C(=O)C1=O', year: 1969, class: 'Anthracycline' },
  { name: 'Paclitaxel', smiles: 'CC1=C2C(C(=O)C1)OC1CC2CCC2(C)C2CC(O)C=CC2OC2C(C)=C1C(=O)O', year: 1992, class: 'Taxane' },
  
  // FDA Approved - CNS/Psychiatric
  { name: 'Sertraline', smiles: 'Clc1ccc2c(c1)C(c1ccc(Cl)cc1)CNC2', year: 1991, class: 'SSRI' },
  { name: 'Fluoxetine', smiles: 'CCC(c1ccc(C(F)(F)F)cc1)NCCOC', year: 1987, class: 'SSRI' },
  { name: 'Escitalopram', smiles: 'CN(C)CC1C2=CC=CC=C2CC1c1ccc(F)cc1', year: 2002, class: 'SSRI' },
  { name: 'Paroxetine', smiles: 'Fc1ccc([C@@H]2CCNC[C@H]2COc2ccc3c(c2)OCO3)cc1', year: 1992, class: 'SSRI' },
  { name: 'Venlafaxine', smiles: 'CCN(CC)CC(c1ccccc1)O', year: 1993, class: 'SNRI' },
  { name: 'Duloxetine', smiles: 'CN(C)CCS(=O)c1ccc2ccccc2c1', year: 2004, class: 'SNRI' },
  { name: 'Amitriptyline', smiles: 'CN(C)CCC=C1c2ccccc2CCc1ccccc1', year: 1961, class: 'TCA' },
  { name: 'Haloperidol', smiles: 'O=C(CCCN1CCC(C(O)(c2ccc(Cl)cc2)c2ccc(Cl)cc2)CC1)c1ccc(F)cc1', year: 1958, class: 'Antipsychotic' },
  { name: 'Risperidone', smiles: 'Clc1ccc(N2CCN(CC2)C(=O)Oc2ccccc2)cc1', year: 1993, class: 'Antipsychotic' },
  { name: 'Quetiapine', smiles: 'O=C1N(CCOc2ccccc2)CCN1CC1=CC=NC=C1', year: 1997, class: 'Antipsychotic' },
  { name: 'Olanzapine', smiles: 'Cc1ccc2c(c1)ncnc2Nc1ccccc1N1CCNC1=O', year: 1996, class: 'Antipsychotic' },
  { name: 'Aripiprazole', smiles: 'Clc1ccc(N2CCN(CC2)C(=O)NC(C)(C)C)cc1', year: 2002, class: 'Antipsychotic' },
  { name: 'Diazepam', smiles: 'CN1C(=O)CN=C(C2=CC=CC=C2)C3=CC=CC=C31', year: 1963, class: 'Benzodiazepine' },
  { name: 'Lorazepam', smiles: 'OC1N=C(c2ccccc2)c2cc(Cl)ccc2N(CC(=O)O)C1c1ccccc1', year: 1977, class: 'Benzodiazepine' },
  { name: 'Alprazolam', smiles: 'Cc1nnc2n1-c1ccc(Cl)cc1C(c1ccccc1)=NC2', year: 1981, class: 'Benzodiazepine' },
  { name: 'Zolpidem', smiles: 'CC(C)N(CC)C(=O)c1cnc2ccc(N)nc12', year: 1983, class: 'Sedative' },
  { name: 'Modafinil', smiles: 'CS(=O)C(C)(C)N1C(=O)NC1=O', year: 1998, class: 'Wake-promoting' },
  { name: 'Phenytoin', smiles: 'O=C1NC(=O)NC1c1ccccc1', year: 1938, class: 'Anticonvulsant' },
  { name: 'Levetiracetam', smiles: 'CCC(C)(C(=O)N)N1CCCC1=O', year: 1999, class: 'Anticonvulsant' },
  { name: 'Lamotrigine', smiles: 'N=c1nnc(N2CCCCC2)nc1Cl', year: 1994, class: 'Anticonvulsant' },
  
  // FDA Approved - Anti-infectives
  { name: 'Amoxicillin', smiles: 'CC1(C)S[C@@H]2[C@H](NC(=O)[C@H](N)c3ccc(O)cc3)C(=O)N2[C@H]1C(=O)O', year: 1972, class: 'Antibiotic' },
  { name: 'Azithromycin', smiles: 'CN(CC)C1OC(C)CC(O)(C)OC1C=CC=CC=CC=O', year: 1991, class: 'Antibiotic' },
  { name: 'Ciprofloxacin', smiles: 'O=C1N2C=CC(=O)C=C2C1N1CCNCC1', year: 1983, class: 'Fluoroquinolone' },
  { name: 'Levofloxacin', smiles: 'C1CCn2c(nc3c(F)cccc3c2=O)C1C(=O)O', year: 1996, class: 'Fluoroquinolone' },

  { name: 'Rifampin', smiles: 'CC1=NC=CC=C1C(=O)NNC(=O)C(C)(C)C1=CC=NO1', year: 1971, class: 'Antibiotic' },
  { name: 'Acyclovir', smiles: 'NC1=NC=NC2=C1NCC2O', year: 1982, class: 'Antiviral' },
  { name: 'Oseltamivir', smiles: 'CCC(C)OC(=O)N1CCC(CC1)C(=O)O', year: 1999, class: 'Antiviral' },
  { name: 'Remdesivir', smiles: 'CCC(CC)COc1ccc(cc1)C(=O)NCC(N)=N', year: 2020, class: 'Antiviral' },
  { name: 'Paxlovid', smiles: 'CC(C)(C)C1=CC=CC=C1C(=O)NCC(N)=N', year: 2021, class: 'Antiviral' },
  { name: 'Ritonavir', smiles: 'CC(C)C1=NC=NC2=C1N=CC(=N2)C(=O)NC(C)(C)C', year: 1996, class: 'Antiviral' },
  { name: 'Dolutegravir', smiles: 'N#CC1=CC2=C(C=C1)C(=NN1CCOC1=O)C2c1ccccc1', year: 2013, class: 'Integrase Inhibitor' },
  { name: 'Tenofovir', smiles: 'CC(C)NCC(C)N1C=NC2=C1C(=O)NCC(=O)O', year: 2001, class: 'Antiviral' },
  { name: 'Fluconazole', smiles: 'OC(Cn1cnc(N1c1ccc(F)cc1Cl)c1ccc(F)cc1)(C(F)(F)F)C(F)(F)F', year: 1981, class: 'Antifungal' },
  { name: 'Itraconazole', smiles: 'Clc1ccc2c(c1)C(Cn1nc3ccccc3n1)N2C(=O)C1=CC=CC=C1', year: 1992, class: 'Antifungal' },
  
  // FDA Approved - Respiratory
  { name: 'Albuterol', smiles: 'CC(C)(C)NCC(O)COc1ccccc1O', year: 1981, class: 'Beta-2 Agonist' },
  { name: 'Fluticasone', smiles: 'S(=O)(=O)CC1SC2C(C1F)C1C(C2=O)C(F)(F)C1C2=CC=CC=C2', year: 1994, class: 'Corticosteroid' },
  { name: 'Montelukast', smiles: 'CC(C)(C)C1=CC=CC=C1C(=O)OCC(O)C1=CC=CC=C1S(=O)(=O)CC1=CC=CC=C1', year: 1998, class: 'Leukotriene Antagonist' },
  { name: 'Tiotropium', smiles: 'C1CC2CCC1N2C(=O)OCC(O)(C)OC', year: 2004, class: 'Anticholinergic' },
  
  // FDA Approved - GI
  { name: 'Omeprazole', smiles: 'COc1ccc2nc(S(=O)(=O)N(C)C)nc2c1', year: 1989, class: 'PPI' },
  { name: 'Pantoprazole', smiles: 'COc1ccc2nc(S(=O)(=O)N3CCN(C)CC3)nc2c1', year: 2001, class: 'PPI' },
  { name: 'Esomeprazole', smiles: 'COc1ccc2nc(S(=O)(=O)N(C)C)nc2c1C', year: 2001, class: 'PPI' },
  { name: 'Ranitidine', smiles: 'CC(C)NCC(=O)NCCNS(=O)(=O)C', year: 1983, class: 'H2 Blocker' },
  { name: 'Famotidine', smiles: 'NCC(=O)NCCS(=O)(=O)N', year: 1983, class: 'H2 Blocker' },
  { name: 'Ondansetron', smiles: 'Clc1ccc2c(c1)C(=O)NCC2N1CCOC', year: 1991, class: 'Antiemetic' },
  { name: 'Metoclopramide', smiles: 'CC(CO)NCC(N)CC1=CC=CC=C1Cl', year: 1975, class: 'Antiemetic' },
  { name: 'Loperamide', smiles: 'ClC1=CC=CC=C1C(C)(C)CCN1CCC(CC1)C(=O)N', year: 1976, class: 'Antidiarrheal' },
  
  // FDA Approved - Thyroid/Hormones
  { name: 'Levothyroxine', smiles: 'NC(Cc1ccc(O)c(I)c1)C(=O)NCC(O)=O', year: 1952, class: 'Thyroid Hormone' },
  { name: 'Prednisone', smiles: 'CC1=CC(=O)C2CCC3C(C2C1O)C(CC3)C(=O)CO', year: 1954, class: 'Corticosteroid' },
  { name: 'Methylprednisolone', smiles: 'CC1=CC(=O)C2CCC3C(C2C1O)C(CC3)C(=O)C', year: 1955, class: 'Corticosteroid' },
  { name: 'Dexamethasone', smiles: 'CC1=CC2=CC(=O)C=CC2=C1F', year: 1958, class: 'Corticosteroid' },
  { name: 'Hydrocortisone', smiles: 'CC1OCC2C3CCC4=CC(=O)CCC4C3C(O)CC12O', year: 1951, class: 'Corticosteroid' },
  { name: 'Spironolactone', smiles: 'CC(=O)SCC(OC)=O', year: 1957, class: 'Mineralocorticoid Antagonist' },
  { name: 'Finasteride', smiles: 'CC1CCC2C(C1CCC2)C(=O)N', year: 1992, class: '5-alpha-Reductase Inhibitor' },
  
  // FDA Approved - Rheumatology
  { name: 'Methotrexate', smiles: 'CNc1ccc2c(c1)C(=O)NCC(=O)NCC(=O)O', year: 1953, class: 'DMARD' },
  { name: 'Sulfasalazine', smiles: 'O=C(Nc1ccc(N=Nc2ccc(S(=O)(=O)N)cc2)cc1)C', year: 1950, class: 'DMARD' },
  { name: 'Hydroxychloroquine', smiles: 'CCN(CC)CCCC(C)N', year: 1955, class: 'DMARD' },
  
  // FDA Approved - Other
  // FDA Approved - Other
  { name: 'Sildenafil', smiles: 'CCCC1=NN=C2N1N=C(C2)N1CCN(CC1)S(=O)(=O)c1ccc(OCC)c(c1)S(=O)(=O)C', year: 1998, class: 'PDE5 Inhibitor' },
  { name: 'Tadalafil', smiles: 'O=C1N(C)CC(=O)N2[C@H]1Cc1c([nH]c3ccccc13)[C@H]2c1ccc2OCOc2c1', year: 2003, class: 'PDE5 Inhibitor' },
  { name: 'Allopurinol', smiles: 'Oc1cc2cn[nH]c2nc1', year: 1966, class: 'Xanthine Oxidase Inhibitor' },
  { name: 'Colchicine', smiles: 'CC(=O)N[C@H]1CCc2cc(OC)c(OC)c(OC)c2-c2ccc(OC)c(=O)cc21', year: 1961, class: 'Gout' },
  { name: 'Isotretinoin', smiles: 'CC1=C(C=CC=C(C)C=CC=C(C)C(=O)O)C(C)(C)CCC1', year: 1982, class: 'Retinoid' },
  { name: 'Mupirocin', smiles: 'CC(C)[C@@H]1CC[C@@H](O)[C@H]1C(=O)O', year: 1987, class: 'Antibiotic' },
  { name: 'Hydroxyzine', smiles: 'OCCONCCN1CCN(C(c2ccccc2)c2ccc(Cl)cc2)CC1', year: 1956, class: 'Antihistamine' },
  { name: 'Cetirizine', smiles: 'OC(=O)COCCN1CCN(C(c2ccccc2)c2ccc(Cl)cc2)CC1', year: 1987, class: 'Antihistamine' },
  { name: 'Loratadine', smiles: 'CCOC(=O)N1CCC(=C2c3ccc(Cl)cc3CCc3cccnc32)CC1', year: 1981, class: 'Antihistamine' },
  { name: 'Rivastigmine', smiles: 'CCN(C)C(=O)Oc1cccc(c1)[C@@H](C)N(C)C', year: 2000, class: 'Cholinesterase Inhibitor' },
  { name: 'Donepezil', smiles: 'COc1cc2c(cc1OC)C(=O)C(CC1CCN(Cc3ccccc3)CC1)C2', year: 1996, class: 'Cholinesterase Inhibitor' },
  { name: 'Memantine', smiles: 'CC12CC3CC(C)(C1)CC(N)(C3)C2', year: 2000, class: 'NMDA Antagonist' },
  { name: 'Gabapentin', smiles: 'NCC1(CC(=O)O)CCCCC1', year: 1993, class: 'Anticonvulsant' },
  { name: 'Pregabalin', smiles: 'C[C@H](CC(=O)O)CN', year: 2005, class: 'Anticonvulsant' },
  
  // Investigational Drugs (no FDA approval year)
  { name: 'Baricitinib', smiles: 'CCS(=O)(=O)N1CC(CC1#N)n1cc(cn1)-c1ncnc2[nH]ccc12', year: 2022, class: 'JAK Inhibitor' },
  { name: 'Tofacitinib', smiles: 'C[C@@H]1CCN(C[C@H]1N(C)c2ncnc3[nH]ccc23)C(=O)CC#N', year: 2012, class: 'JAK Inhibitor' },
  { name: 'Upadacitinib', smiles: 'CC[C@@H]1CN(C1#N)c1cc(c2[nH]cnc2n1)C(=O)N', year: 2019, class: 'JAK Inhibitor' },
  { name: 'Filgotinib', smiles: 'CS(=O)(=O)N1CCN(CC1)c1ccc(nc1)C(=O)N[C@@H]2COCC2', year: 2020, class: 'JAK Inhibitor' },
  { name: 'Deucravacitinib', smiles: 'CN[C@H]1C(=O)N(C)c2cc(ccc21)n3cncc3', year: 2022, class: 'TYK2 Inhibitor' },
  { name: 'Rimegepant', smiles: 'C[C@H](O)[C@@H]1N(Cc2ccc(cc2)-c2n[nH]c(=O)n2C)C(=O)c2ccc(cc2)C1(C)C', year: 2024, class: 'CGRP Antagonist' },
  { name: 'Zavegepant', smiles: 'CC(C)(C)C(=O)N[C@@H]1C(=O)N(C)c2cc(ccc21)n3cncc3', year: 2023, class: 'CGRP Antagonist' },
  { name: 'Voxelotor', smiles: 'Cc1cc(C(=O)O)c(C)c(c1OC)c1ccccc1', year: 2019, class: 'Hemoglobin S Polymerization Inhibitor' },
  { name: 'Lusutrombopag', smiles: 'CCCCc1ccc(cc1)C(=O)Nc1ccc(N2CCCCC2)cc1', year: 2019, class: 'TPO Receptor Agonist' },
  { name: 'Avatrombopag', smiles: 'CCCCc1ccc(cc1)C(=O)Nc1ccc(N2CCCCC2)cc1', year: 2018, class: 'TPO Receptor Agonist' },
  { name: 'Rolapitant', smiles: 'C[C@H]1CN(C[C@@H]1c1cc(F)cc(F)c1)Cc1cc(Cl)cc(Cl)c1', year: 2015, class: 'NK-1 Antagonist' },
  { name: 'Netarsudil', smiles: 'CC(C)CC(C)N[C@@H]1Cc2ccccc2C1', year: 2017, class: 'Rho Kinase Inhibitor' },
];

export function getRandomDrugs(count: number = 4): DrugSuggestion[] {
  const shuffled = [...drugPool].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}
