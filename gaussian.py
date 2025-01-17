"""
/******************************************************************************
  This source file is part of the Avogadro project.

  This source code is released under the New BSD License, (the "License").

******************************************************************************/
"""

import argparse
import json
import sys

# Some globals:
debug = False
warnings = []

option_types={"Title":"string", "Calculation Type":"stringList", "Theory":"stringList",
              "Basis":"stringList", "Filename Base":"string", "Processor Cores":"integer",
              "Memory":"integer", "Multiplicity":"integer", "Charge":"integer",
              "Output Format":"stringList"}

calc_type={"Single Point": " SP",
           "Equilibrium Geometry": " Opt",
           "Frequencies": " Opt Freq"}

theories=['AM1', 'PM3', 'RHF', 'B3LYP', 'WB97XD', 'MP2', 'CCSD']

bases=['STO-3G', '3-21G', '6-31G(d)', '6-31G(d,p)', 'LANL2DZ', 'cc-pVDZ', 'cc-pVTZ',
       'cc-pVQZ', 'cc-pV5Z', 'cc-pV6Z', 'aug-cc-pVDZ', 'aug-cc-pVTZ', 'aug-cc-pVQZ',
       'aug-cc-pV5Z', 'aug-cc-pV6Z', 'Def2SV', 'Def2TZV', 'Def2QZV', 'Def2SVP', 'Def2TZVP',
       'Def2QZVP', 'Def2SVPP', 'Def2TZVPP', 'Def2QZVPP']

def getOptions():
    userOptions = {option:{"type":t} for option,t in option_types.items()}

    userOptions["tabName"]="Standard"
    userOptions['Title']['default'] = ''

    userOptions['Calculation Type']['default'] = 1
    userOptions['Calculation Type']['values'] = [c for c in calc_type]

    userOptions['Theory']['default'] = 3
    userOptions['Theory']['values'] = theories

    userOptions['Basis']['default'] = 2
    userOptions['Basis']['values'] = bases

    altOptions={f"Alternate {k}":{} for k in ("Theory", "Basis Set")}
    altOptions["tabName"]="Alternate"
    altOptions['Alternate Theory']['type'] = 'string'
    altOptions['Alternate Theory']['default'] = ''

    altOptions['Alternate Basis Set']['type'] = 'string'
    altOptions['Alternate Basis Set']['default'] = ''

    userOptions['Filename Base']['default'] = 'job'

    userOptions['Processor Cores']['default'] = 8
    userOptions['Processor Cores']['minimum'] = 1

    userOptions['Memory']['default'] = 28
    userOptions['Memory']['minimum'] = 1

    userOptions['Multiplicity']['default'] = 1
    userOptions['Multiplicity']['minimum'] = 1
    userOptions['Multiplicity']['maximum'] = 5

    userOptions['Charge']['default'] = 0
    userOptions['Charge']['minimum'] = -9
    userOptions['Charge']['maximum'] = 9

    userOptions['Output Format']['default'] = 0
    userOptions['Output Format']['values'] = ['Standard', 'Molden', 'Molekel']

    userOptions['Write Checkpoint File'] = {}
    userOptions['Write Checkpoint File']['type'] = "boolean"
    userOptions['Write Checkpoint File']['default'] = True

    # TODO Coordinate format (need zmatrix)
    userOptions=[userOptions,altOptions]
    opts = {'userOptions': userOptions}

    return opts


def generateInputFile(opts):
    # Extract options:
    title = opts['Title']
    calculate = opts['Calculation Type']
    theory = opts['Theory']
    if opts["Alternate Theory"]:
        theory = opts["Alternate Theory"]
    basis = opts['Basis']
    if opts['Alternate Basis Set']:
        basis = opts['Alternate Basis Set']
    multiplicity = opts['Multiplicity']
    charge = opts['Charge']
    outputFormat = opts['Output Format']
    checkpoint = opts['Write Checkpoint File']
    nCores = opts['Processor Cores']

    output = ''

    # Number of cores
    output += f"%NProcShared={nCores}\n"
    output += f"%mem={opts['Memory']}GB\n"

    # Checkpoint
    if checkpoint:
        baseName=opts["Filename Base"]
        output += f'%Chk={baseName}.chk\n'

    # Theory/Basis
    if theory in ('AM1','PM3'):
        output += f'#p {theory}'
        warnings.append('Ignoring basis set for semi-empirical calculation.')
    else:
        output += f"#p {theory}/{basis.replace(' ', '')}" 

    # Calculation type
    try:
        output += calc_type[calculate]
    except KeyError:
        raise Exception(f'Invalid calculation type: {calculate}')

    # Output format
    if outputFormat == 'Standard':
        pass
    elif outputFormat == 'Molden':
        output += ' gfprint pop=full'
    elif outputFormat == 'Molekel':
        output += ' gfoldprint pop=full'
    else:
        raise Exception(f'Invalid output format: {outputFormat}')

    # Title
    output += f'\n\n {title}\n\n'

    # Charge/Multiplicity
    output += f"{charge} {multiplicity}\n"

    # Coordinates
    output += '$$coords:Sxyz$$\n'

    # The gaussian code is irritatingly fickle -- it *will* silently crash if
    # this extra, otherwise unnecessary newline is not present at the end of the
    # file.
    output += '\n'

    return output


def generateInput():
    # Read options from stdin
    stdinStr = sys.stdin.read()

    # Parse the JSON strings
    opts = json.loads(stdinStr)

    # Generate the input file
    inp = generateInputFile(opts['options'])

    # Basename for input files:
    baseName = opts['options']['Filename Base']

    # Prepare the result
    # Specify the main input file. This will be used by MoleQueue to determine
    # the value of the $$inputFileName$$ and $$inputFileBaseName$$ keywords.
    result = {"mainFile": f'{baseName}.gjf'}
    # Input file text -- will appear in the same order in the GUI as they are
    # listed in the array:
    files = [{'filename': f'{baseName}.gjf', 'contents': inp}]
    if debug:
        files.append({'filename': 'debug_info', 'contents': stdinStr})
    result['files'] = files

    if len(warnings) > 0:
        result['warnings'] = warnings

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser('Generate a Gaussian input file.')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--print-options', action='store_true')
    parser.add_argument('--generate-input', action='store_true')
    parser.add_argument('--display-name', action='store_true')
    parser.add_argument('--lang', nargs='?', default='en')
    args = vars(parser.parse_args())

    debug = args['debug']

    if args['display_name']:
        print("Gaussian")
    if args['print_options']:
        print(json.dumps(getOptions()))
    elif args['generate_input']:
        print(json.dumps(generateInput()))
