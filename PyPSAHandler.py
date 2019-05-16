from pypsa import Network

import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

class PyPSAHandler:
    _network = Network

    def __init__(self, apiReqBody):
        self._network = self._buildNetwork(apiReqBody)
        # TODO: consistency check door PyPSA uit laten voeren: https://pypsa.org/doc/troubleshooting.html

    @staticmethod
    def validate(apiReqBody):
        if(isinstance(apiReqBody, dict) is not True):
            return "Request body format is invalid"

        if('components' not in apiReqBody):
            return "There are no components specified"

        if(isinstance(apiReqBody['components'], list) is not True):
            return "\"components\" in the request body is not a (valid) list"

        if(len(apiReqBody['components']) <= 0):
            return "There are no components specified"

        componentIds = []
        for component in apiReqBody['components']:

            # TODO: controleren of het id en de p wel een nummer is
            if('id' not in component or 'p' not in component):
                return "Not for all the components is a (valid) id or p submitted"

            if(component['id'] in componentIds):
                return "There is a duplicate id submitted for a component (id: {})".format(component['id'])

            componentIds.append(component['id'])


        if('lines' not in apiReqBody):
            return "There are no lines specified"

        if (isinstance(apiReqBody['lines'], list) is not True):
            return "\"lines\" in the request body is not a (valid) list"

        if(len(apiReqBody['lines']) <= 0):
            return "There are no lines specified"

        lineIds = []
        for line in apiReqBody['lines']:

            # TODO: controleren of alle variabelen wel van van het juiste type zijn
            if ('id' not in line or 'start' not in line or 'end' not in line or 'p' not in line):
                return "Not for all the lines is a (valid) id, start, end or p submitted"

            # TODO: controleren of p wel een positief getal is

            if (line['id'] in lineIds):
                return "There is a duplicate id submitted for a line (id: {})".format(line.id)

            if (line['start'] not in componentIds or line['end'] not in componentIds):
                return "The component with id {} or {} does not exist for the line {}.".format(line['start'],
                                                                                               line['end'], line['id'])

            if (line['start'] == line['end']):
                return "The component at the start of the line can not be the same as the component at the end of the line."

            # TODO: controleren of er niet twee of meerdere lines zijn die naar dezelfde componenten gaan

            lineIds.append(line['id'])

        return None

    def _buildNetwork(self, apiReqBody):
        network = Network()

        # TODO: implementeren dat de van het component wordt gebruikt (ivm de netheid van de CSV-export)
        if('components' in apiReqBody):
            for component in apiReqBody['components']:

                if(component['p'] > 0): # Generator because power is a positive value
                    network.add('Bus', 'bus_{}'.format(component['id']))
                    network.add('Generator',
                                      'gen_{}'.format(component['id']),
                                      bus = 'bus_{}'.format(component['id']),
                                      p_nom = component['p'])

                else: # Load because power is a negative value
                    network.add('Bus', 'bus_{}'.format(component['id']))
                    network.add('Load',
                                      'load_{}'.format(component['id']),
                                      bus = 'bus_{}'.format(component['id']),
                                      p_set = -component['p'])

        if('lines' in apiReqBody):
            for line in apiReqBody['lines']:
                network.add("Line",
                                  'line_{}_{}-{}'.format(line['id'], line['start'], line['end']),
                                  bus0 = 'bus_{}'.format(line['start']),
                                  bus1 = 'bus_{}'.format(line['end']),
                                  x = 0.0001,
                                  s_nom = line['p'])

        return network

    def calculate(self):
        self._network.lopf()

        currentThrougLines = self._network.lines_t.p0

        if(currentThrougLines.empty):
            return None

        currentThrougLines = self._network.lines_t.p0.iloc[0]
        percentOfLinesInUse = (abs(self._network.lines_t.p0 / self._network.lines.s_nom) * 100).iloc[0]

        apiResponse = {
            'lines': [
            ]
        }

        for lineName in list(currentThrougLines.index):
            lineId = lineName.split('_')[1]
            apiResponse['lines'].append({
                'id': int(lineId),
                'percentInUse': round(percentOfLinesInUse[lineName] * 100) / 100,
                'powerThrough': currentThrougLines[lineName]
            })

        return apiResponse