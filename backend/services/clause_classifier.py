class ClauseClassifier:

    def __init__(self, formatter):
        self.formatter = formatter

    def classify(self, context):
        formatted = self.formatter.format(context)
        print("Formatted Context for Classification:")
        print(formatted)