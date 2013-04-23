@QUANTUMINPUT_PYTHON2_SHEBANG@

"""
/******************************************************************************

  This source file is part of the Avogadro project.

  Copyright 2013 Kitware, Inc.

  This source code is released under the New BSD License, (the "License").

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

******************************************************************************/
"""

import argparse
import json
import sys

# Some globals:
targetName = 'GAMESS-UK'
debug = False

def getOptions():
  userOptions = {}

  userOptions['Title'] = {}
  userOptions['Title']['type'] = 'string'
  userOptions['Title']['default'] = ''

  userOptions['Calculation Type'] = {}
  userOptions['Calculation Type']['type'] = "stringList"
  userOptions['Calculation Type']['default'] = 1
  userOptions['Calculation Type']['values'] = \
    ['Single Point', 'Equilibrium Geometry', 'Frequencies', 'Transition State']

  userOptions['Theory'] = {}
  userOptions['Theory']['type'] = "stringList"
  userOptions['Theory']['default'] = 2
  userOptions['Theory']['values'] = \
    ['RHF', 'MP2', 'B3LYP', 'BLYP', 'SVWN', 'B97', 'HCTH', 'FT97']

  userOptions['Basis'] = {}
  userOptions['Basis']['type'] = "stringList"
  userOptions['Basis']['default'] = 2
  userOptions['Basis']['values'] = \
    ['STO-3G', '3-21G', '6-31G', '6-31G(d)', 'cc-pVDZ', 'cc-pVTZ']

  userOptions['Charge'] = {}
  userOptions['Charge']['type'] = "integer"
  userOptions['Charge']['default'] = 0
  userOptions['Charge']['minimum'] = -9
  userOptions['Charge']['maximum'] = 9

  userOptions['Multiplicity'] = {}
  userOptions['Multiplicity']['type'] = "integer"
  userOptions['Multiplicity']['default'] = 1
  userOptions['Multiplicity']['minimum'] = 1
  userOptions['Multiplicity']['maximum'] = 6

  # TODO Coordinate format (need zmatrix)

  userOptions['Direct SCF Mode'] = {}
  userOptions['Direct SCF Mode']['type'] = 'boolean'
  userOptions['Direct SCF Mode']['default'] = False

  opts = {'userOptions' : userOptions}
  opts['allowCustomBaseName'] = True

  return opts

def generateInputFile(opts, settings):
  # Extract options:
  title = opts['Title']
  calculate = opts['Calculation Type']
  theory = opts['Theory']
  basis = opts['Basis']
  charge = opts['Charge']
  multiplicity = opts['Multiplicity']
  directScf = opts['Direct SCF Mode']

  # Convert to code-specific strings
  calcStr = ''
  if calculate == 'Single Point':
    calcStr = 'scf'
  elif calculate == 'Equilibrium Geometry':
    calcStr = 'optxyz' # TODO If we add zmatrix, this will need updating.
  elif calculate == 'Frequencies':
    calcStr = 'hessian'
  elif calculate == 'Transition State':
    calcStr = 'saddle'
  else:
    raise Exception('Unhandled calculation type: %s'%calculate)

  theoryStr = ''
  if theory in ['RHF', 'MP2']:
    theoryStr = 'scftype '
    if directScf:
      theoryStr += 'direct '
    theoryStr += theory.lower()
  elif theory in ['B3LYP', 'BLYP', 'SVWN', 'B97', 'HCTH', 'FT97']:
    if directScf:
      theoryStr += 'scftype direct\n'
    theoryStr += 'dft %s'%theory.lower()
  else:
    raise Exception('Unhandled theory type: %s'%theory)

  basisStr = ''
  if basis == 'STO-3G':
    basisStr = 'sto3g'
  elif basis == '6-31G(d)':
    basisStr = '6-31G*'
  elif basis in ['3-21G', '6-31G', 'cc-pVDZ', 'cc-pVTZ']:
    basisStr = basis
  else:
    raise Exception('Unhandled basis type: %s'%basis)

  output = ''

  # Copied from 1.x extension. Seems useful.
  output += '# This file was generated by Avogadro\n'
  output += '# For more GAMESS-UK input options consult the manual at:\n'
  output += '# http://www.cfs.dl.ac.uk/docs/index.shtml\n\n'

  output += 'title\n%s\n\n'%title

  if calculate in ['Equilibrium Geometry', 'Transition State']:
    output += '# Ensure orbital vectors printed after optimization:\n'
    output += 'iprint vectors\n\n'

  output += 'mult %d\ncharge %d\n\n'%(multiplicity, charge)

  output += 'geometry angstrom'
  if calculate == 'Transition State':
    output += ' all'
  output += '\n'

  output += '$$coords:_xyzZS$$\nend\n\n'

  output += 'basis %s\n\n'%basisStr

  output += 'runtype %s\n'%calcStr
  output += '%s\n\n'%theoryStr

  output += 'enter\n'

  return output

def generateInput():
  # Read options from stdin
  stdinStr = sys.stdin.read()

  # Parse the JSON strings
  opts = json.loads(stdinStr)

  # Generate the input file
  inp = generateInputFile(opts['options'], opts['settings'])

  # Basename for input files:
  baseName = opts['settings']['baseName']

  # Prepare the result
  result = {}
  # Input file text -- will appear in the same order in the GUI as they are
  # listed in the array:
  files = []
  files.append({'filename': '%s.gukin'%baseName, 'contents': inp})
  if debug:
    files.append({'filename': 'debug_info', 'contents': stdinStr})
  result['files'] = files
  # Specify the main input file. This will be used by MoleQueue to determine
  # the value of the $$inputFileName$$ and $$inputFileBaseName$$ keywords.
  result['mainFile'] = '%s.gukin'%baseName
  return result

if __name__ == "__main__":
  parser = argparse.ArgumentParser('Generate a %s input file.'%targetName)
  parser.add_argument('--debug', action='store_true')
  parser.add_argument('--print-options', action='store_true')
  parser.add_argument('--generate-input', action='store_true')
  parser.add_argument('--display-name', action='store_true')
  args = vars(parser.parse_args())

  debug = args['debug']

  if args['display_name']:
    print(targetName)
  if args['print_options']:
    print(json.dumps(getOptions()))
  elif args['generate_input']:
    print(json.dumps(generateInput()))
