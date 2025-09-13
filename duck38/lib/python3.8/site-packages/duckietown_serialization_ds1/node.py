# language=yaml
config = """
~Component:
    # static assets are to be ready before the initialization
    assets:
        map:
            ~StaticAsset:
                description:
                type: "~PlacedObject"

    inputs:
        query:
            ~InputStream:
                description:
                type: "~SE2Transform"
                expect-frequency: whenever

        timer1:
            ~Timer:
                interval: 5s

    ui-commands:
        go:
            ~Command:
                description: Control the robot
                in_states: [running]

        stop:
            ~Command:
                description: Stops the motion
                in_states: [running]

    outputs:
        result:
            ~OutputStream:
                description:
                type: "~PlanningResult"

        processed:
            ~Visualization:
                type: "~ProcessedImage"

        status:
            ~Visualization:

    configuration:
        param1:
            ~ConfigurationParameter:
                description:
                default:
                type:

    states:
        ~States:
            born:
            init:
              ~States:
                  nominal:
                  failed:
                    will-retry:
                    given-up:
            running:
                nominal:
                    waiting:
                    reading:
                    computing:
                    writing:
                failed:
            terminating:
                nominal:
                failed:
            done:

    resources:
      computation:
      latency:

"""
# language=yaml
interc = """
~Interconnection:
    components:
        component1: {~FromConfig: a.yaml}

    links: |
        component1.z -> component2.z
        mine -> component1.z

    inputs:
        map: component1.map

    outputs:
        two: component2.data

    commands:
        go: component1.go


"""


class MessagingInterface(object):
    """


    DSC= {"

    """

    @classmethod
    def from_env(cls):
        pass

    def __init__(self):
        pass


# # class Envelope(object):
# #     name =
# class NodeTest():
#
#     def handle_message_map(self, envelope, data):
#         pass
#
#     def __init__(self):
#         mi = MessagingInterface.from_env()
#         mi.inputs(message=handle_message)
#
#
# def register(message=self.handle_message,
#              )
