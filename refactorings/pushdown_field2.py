import logging

try:
    import understand as und
except ImportError as e:
    print(e)

from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener

from refactorings.utils.utils2 import parse_and_walk

logger = logging.getLogger()
__author__ = "Seyyed Ali Ayati"


class CutFieldListener(JavaParserLabeledListener):
    def __init__(self, source_class, field_name, rewriter: TokenStreamRewriter):
        """
        Removes the field declaration from the parent class.

        Args:
            source_class: (str) Parent's class name.
            field_name: (str) Field's name.
            rewriter: Antlr's token stream rewriter.
        Returns:
            field_content: The full string of field declaration
        """
        self.source_class = source_class
        self.field_name = field_name
        self.rewriter = rewriter
        self.field_content = ""
        self.import_statements = ""

        self.detected_field = False
        self.is_source_class = False

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        class_name = ctx.IDENTIFIER().getText()
        if class_name == self.source_class:
            self.is_source_class = True

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        class_name = ctx.IDENTIFIER().getText()
        if self.is_source_class and class_name == self.source_class:
            self.is_source_class = False

    def enterImportDeclaration(self, ctx: JavaParserLabeled.ImportDeclarationContext):
        statement = self.rewriter.getText(
            program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
            start=ctx.start.tokenIndex,
            stop=ctx.stop.tokenIndex
        )
        self.import_statements += statement + "\n"

    def exitVariableDeclaratorId(self, ctx: JavaParserLabeled.VariableDeclaratorIdContext):
        variable_name = ctx.IDENTIFIER().getText()
        if self.is_source_class:
            if variable_name == self.field_name:
                self.detected_field = True

    def exitClassBodyDeclaration2(self, ctx: JavaParserLabeled.ClassBodyDeclaration2Context):
        if self.detected_field and self.is_source_class:
            self.field_content = self.rewriter.getText(
                program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
                start=ctx.start.tokenIndex,
                stop=ctx.stop.tokenIndex
            )
            self.rewriter.delete(
                program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
                from_idx=ctx.start.tokenIndex,
                to_idx=ctx.stop.tokenIndex
            )
            self.detected_field = False


class PasteFieldListener(JavaParserLabeledListener):
    def __init__(self, source_class, field_content, import_statements, rewriter: TokenStreamRewriter):
        """
        Inserts field declaration to children classes.
        Args:
            source_class: Child class name.
            field_content: Full string of the field declaration.
            rewriter: Antlr's token stream rewriter.
        Returns:
            None
        """
        self.source_class = source_class
        self.rewriter = rewriter
        self.field_content = field_content
        self.import_statements = import_statements
        self.is_source_class = False

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        class_name = ctx.IDENTIFIER().getText()
        if class_name == self.source_class:
            self.is_source_class = True

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        class_name = ctx.IDENTIFIER().getText()
        if self.is_source_class and class_name == self.source_class:
            self.is_source_class = False

    def exitPackageDeclaration(self, ctx: JavaParserLabeled.PackageDeclarationContext):
        self.rewriter.insertAfter(
            program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
            index=ctx.stop.tokenIndex,
            text="\n" + self.import_statements
        )

    def enterClassBody(self, ctx: JavaParserLabeled.ClassBodyContext):
        if self.is_source_class:
            self.rewriter.insertAfter(
                index=ctx.start.tokenIndex,
                text="\n\t" + self.field_content
            )


def main(udb_path, source_package, source_class, field_name, target_classes: list, *args, **kwargs):
    db = und.open(udb_path)
    source_class_ents = db.lookup(f"{source_package}.{source_class}", "Class")
    target_class_ents = []
    source_class_ent = None

    if len(source_class_ents) == 0:
        logger.error(f"Cannot find source class: {source_class}")
        return
    else:
        for ent in source_class_ents:
            if ent.simplename() == source_class:
                source_class_ent = ent
                break
    if source_class_ent is None:
        logger.error(f"Cannot find source class: {source_class}")
        return

    field_ent = db.lookup(f"{source_package}.{source_class}.{field_name}", "Variable")
    if len(field_ent) == 0:
        logger.error(f"Cannot find field to pushdown: {field_name}")
        return
    else:
        field_ent = field_ent[0]

    for ref in source_class_ent.refs("extendBy"):
        if ref.ent().simplename() not in target_classes:
            logger.error("Target classes are not children classes")
            return
        target_class_ents.append(ref.ent())

    for ref in field_ent.refs("useBy, setBy"):
        if ref.file().simplename().split(".")[0] in target_classes:
            continue
        else:
            logger.error("Field has dependencies.")
            return
            # Remove field from source class
    listener = parse_and_walk(
        file_path=source_class_ent.parent().longname(),
        listener_class=CutFieldListener,
        has_write=True,
        source_class=source_class,
        field_name=field_name,
        debug=False
    )
    # Insert field in children classes
    for target_class in target_class_ents:
        parse_and_walk(
            file_path=target_class.parent().longname(),
            listener_class=PasteFieldListener,
            has_write=True,
            source_class=target_class.simplename(),
            field_content=listener.field_content,
            import_statements=listener.import_statements,
            debug=False
        )
    db.close()


if __name__ == '__main__':
    main(
        udb_path="D:\Dev\JavaSample\JavaSample\JavaSample.und",
        source_class="Person",
        source_package="target_package",
        field_name="testField",
        target_classes=["PersonChild"]
    )
