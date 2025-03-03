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


class CutMethodListener(JavaParserLabeledListener):
    def __init__(self, source_class, method_name, rewriter: TokenStreamRewriter):
        """
        Removes the method declaration from the parent class.

        Args:
            source_class: (str) Parent's class name.
            method_name: (str) Method's name.
            rewriter: Antlr's token stream rewriter.
        Returns:
            field_content: The full string of method declaration
        """
        self.source_class = source_class
        self.method_name = method_name
        self.rewriter = rewriter
        self.method_content = ""
        self.import_statements = ""

        self.detected_method = False
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

    def exitMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        if self.is_source_class and ctx.IDENTIFIER().getText() == self.method_name:
            self.detected_method = True

    def exitClassBodyDeclaration2(self, ctx: JavaParserLabeled.ClassBodyDeclaration2Context):
        if self.detected_method:
            self.method_content = self.rewriter.getText(
                program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
                start=ctx.start.tokenIndex,
                stop=ctx.stop.tokenIndex
            )
            self.rewriter.delete(
                program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
                from_idx=ctx.start.tokenIndex,
                to_idx=ctx.stop.tokenIndex
            )
            self.detected_method = False


class PasteMethodListener(JavaParserLabeledListener):
    def __init__(self, source_class, method_content, import_statements, rewriter: TokenStreamRewriter):
        """
        Inserts method declaration to children classes.
        Args:
            source_class: Child class name.
            method_content: Full string of the method declaration.
            rewriter: Antlr's token stream rewriter.
        Returns:
            None
        """
        self.source_class = source_class
        self.rewriter = rewriter
        self.method_content = method_content
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
            self.rewriter.insertBefore(
                program_name=self.rewriter.DEFAULT_PROGRAM_NAME,
                index=ctx.stop.tokenIndex,
                text="\n\t" + self.method_content + "\n"
            )


def main(udb_path, source_package, source_class, method_name, target_classes: list, *args, **kwargs):
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

    method_ent = db.lookup(f"{source_package}.{source_class}.{method_name}", "Method")
    if len(method_ent) == 0:
        logger.error(f"Cannot find method to pushdown: {method_name}")
        return
    else:
        method_ent = method_ent[0]

    for ref in source_class_ent.refs("extendBy"):
        if ref.ent().simplename() not in target_classes:
            logger.error("Target classes are not children classes")
            return
        target_class_ents.append(ref.ent())

    for ref in method_ent.refs("callBy"):
        if ref.file().simplename().split(".")[0] in target_classes:
            continue
        else:
            logger.error("Method has dependencies.")
            return

    # Remove field from source class
    listener = parse_and_walk(
        file_path=source_class_ent.parent().longname(),
        listener_class=CutMethodListener,
        has_write=True,
        source_class=source_class,
        method_name=method_name,
        debug=False
    )
    # Insert field in children classes
    for target_class in target_class_ents:
        parse_and_walk(
            file_path=target_class.parent().longname(),
            listener_class=PasteMethodListener,
            has_write=True,
            source_class=target_class.simplename(),
            method_content=listener.method_content,
            import_statements=listener.import_statements,
            debug=False
        )
    db.close()


if __name__ == '__main__':
    main(
        udb_path="D:\Dev\JavaSample\JavaSample\JavaSample.und",
        source_class="Person",
        source_package="target_package",
        method_name="runTest",
        target_classes=["PersonChild"]
    )
