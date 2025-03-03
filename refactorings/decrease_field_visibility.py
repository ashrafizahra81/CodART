import logging

from refactorings.utils.utils2 import parse_and_walk

try:
    import understand as und
except ImportError as e:
    print(e)

from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener

logger = logging.getLogger()
__author__ = "Seyyed Ali Ayati"


class DecreaseFieldVisibilityListener(JavaParserLabeledListener):
    def __init__(self, source_class, source_field, rewriter: TokenStreamRewriter):
        self.source_class = source_class
        self.source_field = source_field
        self.in_class = False
        self.in_field = False
        self.detected_field = False
        self.rewriter = rewriter

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if ctx.IDENTIFIER().getText() == self.source_class:
            self.in_class = True

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if ctx.IDENTIFIER().getText() == self.source_class:
            self.in_class = False

    def enterFieldDeclaration(self, ctx: JavaParserLabeled.FieldDeclarationContext):
        self.in_field = True

    def exitFieldDeclaration(self, ctx: JavaParserLabeled.FieldDeclarationContext):
        self.in_field = False

    def enterVariableDeclaratorId(self, ctx: JavaParserLabeled.VariableDeclaratorIdContext):
        if ctx.IDENTIFIER().getText() == self.source_field and self.in_field:
            self.detected_field = True

    def exitClassBodyDeclaration2(self, ctx: JavaParserLabeled.ClassBodyDeclaration2Context):
        if self.detected_field:
            self.rewriter.replaceSingleToken(
                token=ctx.modifier(0).start,
                text="private"
            )
            self.detected_field = False


def main(udb_path, source_package, source_class, source_field, *args, **kwargs):
    db = und.open(udb_path)
    field_ent = db.lookup(f"{source_package}.{source_class}.{source_field}", "Variable")

    if len(field_ent) == 0:
        logger.error("Invalid inputs.")
        return
    field_ent = field_ent[0]

    if field_ent.simplename() != source_field:
        logger.error("Invalid entity.")
        return

    if not field_ent.kind().check("Public"):
        logger.error("Field is not public.")
        return

    for ref in field_ent.refs("UseBy,SetBy"):
        ent = ref.ent()
        if f"{source_package}.{source_class}" not in ent.longname():
            logger.debug(f"{source_package}.{source_class} not in {ent.longname()}")
            logger.error("Field cannot set to private.")
            return

    parent = field_ent.parent()
    while parent.parent() is not None:
        parent = parent.parent()

    main_file = parent.longname()
    parse_and_walk(
        file_path=main_file,
        listener_class=DecreaseFieldVisibilityListener,
        has_write=True,
        source_class=source_class,
        source_field=source_field
    )
    db.close()


if __name__ == '__main__':
    main(
        udb_path="D:/IdeaProjects/JSON20201115/JSON20201115.und",
        source_package="org.json",
        source_class="JSONObject",
        source_field="Object"
    )
