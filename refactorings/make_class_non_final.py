from gen.javaLabeled.JavaLexer import JavaLexer

try:
    import understand as und
except ImportError as e:
    print(e)

from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


class MakeNonFinalClassRefactoringListener(JavaParserLabeledListener):
    """
    To implement extract class refactoring based on its actors.
    Creates a new class and move fields and methods from the old class to the new one
    """

    def __init__(self, common_token_stream: CommonTokenStream = None, class_name: str = None):


        if common_token_stream is None:
            raise ValueError('common_token_stream is None')
        else:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)

        if class_name is None:
            raise ValueError("source_class is None")
        else:
            self.objective_class = class_name

        self.is_objective_class = False

        self.detected_field = None
        self.detected_method = None
        self.TAB = "\t"
        self.NEW_LINE = "\n"
        self.code = ""
    def enterTypeDeclaration(self, ctx:JavaParserLabeled.TypeDeclarationContext):


        if  self.objective_class == ctx.classDeclaration().IDENTIFIER().getText():
            #modifier=ctx.getText().split(",")
            is_fanal=False
            for i in range (0, len(ctx.classOrInterfaceModifier())):
             if ctx.classOrInterfaceModifier(i).getText()=="final":
               self.token_stream_rewriter.replaceRange(
               from_idx=ctx.classOrInterfaceModifier(i).start.tokenIndex,
               to_idx=ctx.classOrInterfaceModifier(i).stop.tokenIndex,
               text=""
                )



    # def enterFieldDeclaration(self, ctx:JavaParserLabeled.FieldDeclarationContext):
    #     if self.is_source_class:
    #         #get list of variable and check
    #         class_identifier = ctx.variableDeclarators().getText().split(",")
    #         if "f" in  class_identifier:
    #             ctx1=ctx.parentCtx.parentCtx
    #             start_index = ctx1.start.tokenIndex
    #             stop_index = ctx1.stop.tokenIndex
    #             self.field_text = self.token_stream_rewriter.getText(
    #                 program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
    #                 start=start_index,
    #                 stop=stop_index)
    #
    #             self.token_stream_rewriter.delete(
    #                 program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
    #                 from_idx=ctx1.start.tokenIndex,
    #                 to_idx=ctx1.stop.tokenIndex
    #             )
    #         print(self.field_text)
    #
    # def enterClassDeclaration(self, ctx:JavaParserLabeled.ClassDeclarationContext):
    #     #get class name and check
    #     class_identifier = ctx.IDENTIFIER().getText()
    #     if class_identifier == self.objective_class:
    #         self.is_objective_class = True
    #         print('mids')
    #     else:
    #         self.is_objective_class = False
    # #
    # def enterClassBody(self, ctx: JavaParserLabeled.ClassBodyContext):
    #     ctx1=ctx.parentCtx
    #     class_identifier = ctx1.IDENTIFIER().getText()
    #     if class_identifier in self.children_class:
    #         # if not self.is_source_class:
    #             self.token_stream_rewriter.replaceRange(
    #                 from_idx=ctx.start.tokenIndex+1,
    #                 to_idx=ctx.start.tokenIndex+1,
    #                 text="\n"+self.field_text+"\n"
    #             )


if __name__ == '__main__':
    udb_path = "/home/ali/Desktop/code/TestProject/TestProject.udb"
    source_class = "Triangle"
    # initialize with understand
    main_file = ""
    db = und.open(udb_path)
    for cls in db.ents("class"):
        if cls.simplename() == source_class:
            main_file = cls.parent().longname()
    db.close()
    stream = FileStream(main_file, encoding='utf8')
    lexer = JavaLexer(stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParserLabeled(token_stream)
    parser.getTokenStream()
    parse_tree = parser.compilationUnit()
    my_listener = MakeNonFinalClassRefactoringListener(common_token_stream=token_stream,
                                                       class_name=source_class)
    walker = ParseTreeWalker()
    walker.walk(t=parse_tree, listener=my_listener)

    with open(main_file, mode='w', newline='') as f:
        f.write(my_listener.token_stream_rewriter.getDefaultText())
