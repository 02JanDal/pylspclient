from typing import Any, Literal, Optional
from pydantic import ValidationError
from .lsp_endpoint import LspEndpoint
from .lsp_pydantic_structs import (
    ClientCapabilities,
    ReferenceContext,
    TextDocumentItem,
    TextDocumentIdentifier,
    DocumentSymbol,
    SymbolInformation,
    LocationLink,
    Location,
    Position,
    SignatureHelp,
    CompletionContext,
    CompletionItem,
    CompletionList,
    WorkspaceEdit,
    TextEdit,
)


class LspClient(object):
    def __init__(self, lsp_endpoint: LspEndpoint):
        """
        Constructs a new LspClient instance.

        :param lsp_endpoint:
        """
        self.lsp_endpoint = lsp_endpoint

    def initialize(
        self,
        processId: Optional[int] = None,
        rootPath: Optional[str] = None,
        rootUri: Optional[str] = None,
        initializationOptions: Optional[Any] = None,
        capabilities: Optional[ClientCapabilities | dict] = None,
        trace: Optional[str | Literal["off", "messages", "verbose"]] = None,
        workspaceFolders: Optional[list] = None,
    ):
        """
        The initialize request is sent as the first request from the client to the server. If the server receives a request or notification
        before the initialize request it should act as follows:

        1. For a request the response should be an error with code: -32002. The message can be picked by the server.
        2. Notifications should be dropped, except for the exit notification. This will allow the exit of a server without an initialize request.

        Until the server has responded to the initialize request with an InitializeResult, the client must not send any additional requests or
        notifications to the server. In addition the server is not allowed to send any requests or notifications to the client until it has responded
        with an InitializeResult, with the exception that during the initialize request the server is allowed to send the notifications window/showMessage,
        window/logMessage and telemetry/event as well as the window/showMessageRequest request to the client.

        The initialize request may only be sent once.

        :param int processId: The process Id of the parent process that started the server. Is null if the process has not been started by another process.
                                If the parent process is not alive then the server should exit (see exit notification) its process.
        :param str rootPath: The rootPath of the workspace. Is null if no folder is open. Deprecated in favour of rootUri.
        :param str rootUri: The rootUri of the workspace. Is null if no folder is open. If both `rootPath` and `rootUri` are set
                                    `rootUri` wins.
        :param any initializationOptions: User provided initialization options.
        :param ClientCapabilities capabilities: The capabilities provided by the client (editor or tool).
        :param Trace trace: The initial trace setting. If omitted trace is disabled ('off').
        :param list workspaceFolders: The workspace folders configured in the client when the server starts. This property is only available if the client supports workspace folders.
                                        It can be `null` if the client supports workspace folders but none are configured.
        """
        if capabilities is None:
            raise ValueError("capabilities is required")
        self.lsp_endpoint.start()
        return self.lsp_endpoint.call_method(
            "initialize",
            processId=processId,
            rootPath=rootPath,
            rootUri=rootUri,
            initializationOptions=initializationOptions,
            capabilities=capabilities if isinstance(capabilities, dict) else capabilities.model_dump(by_alias=True),
            trace=trace,
            workspaceFolders=workspaceFolders,
        )

    def initialized(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lsp_endpoint.send_notification("initialized")

    def shutdown(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lsp_endpoint.stop()
        return self.lsp_endpoint.call_method("shutdown")

    def exit(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lsp_endpoint.send_notification("exit")

    def didOpen(self, textDocument: TextDocumentItem):
        """
        The document open notification is sent from the client to the server to signal newly opened text documents. The document's truth is
        now managed by the client and the server must not try to read the document's truth using the document's uri. Open in this sense
        means it is managed by the client. It doesn't necessarily mean that its content is presented in an editor. An open notification must
        not be sent more than once without a corresponding close notification send before. This means open and close notification must be
        balanced and the max open count for a particular textDocument is one. Note that a server's ability to fulfill requests is independent
        of whether a text document is open or closed.

        The DidOpenTextDocumentParams contain the language id the document is associated with. If the language Id of a document changes, the
        client needs to send a textDocument/didClose to the server followed by a textDocument/didOpen with the new language id if the server
        handles the new language id as well.

        :param TextDocumentItem textDocument: The document that was opened.
        """
        self.lsp_endpoint.send_notification(
            "textDocument/didOpen", textDocument=textDocument
        )

    def didChange(self, textDocument: TextDocumentItem, contentChanges):
        """
        The document change notification is sent from the client to the server to signal changes to a text document.
        In 2.0 the shape of the params has changed to include proper version numbers and language ids.

        :param VersionedTextDocumentIdentifier textDocument: The initial trace setting. If omitted trace is disabled ('off').
        :param TextDocumentContentChangeEvent[] contentChanges: The actual content changes. The content changes describe single state changes
            to the document. So if there are two content changes c1 and c2 for a document in state S then c1 move the document
            to S' and c2 to S''.
        """
        self.lsp_endpoint.send_notification(
            "textDocument/didChange",
            textDocument=textDocument,
            contentChanges=contentChanges,
        )

    def documentSymbol(
        self, textDocument: TextDocumentIdentifier
    ) -> list[DocumentSymbol] | list[SymbolInformation]:
        """
        The document symbol request is sent from the client to the server to return a flat list of all symbols found in a given text document.
        Neither the symbol's location range nor the symbol's container name should be used to infer a hierarchy.

        :param TextDocumentItem textDocument: The text document.
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/documentSymbol", textDocument=textDocument.dict()
        )
        try:
            return [DocumentSymbol.model_validate(sym) for sym in result_dict]
        except ValidationError:
            return [SymbolInformation.model_validate(sym) for sym in result_dict]

    def typeDefinition(
        self, textDocument: TextDocumentIdentifier, position: Position
    ) -> list[Location] | None:
        """
        The goto type definition request is sent from the client to the server to resolve the type definition location of a symbol at a given text document position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document.
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/typeDefinition", textDocument=textDocument, position=position
        )
        if result_dict is None:
            return None
        return [Location.model_validate(result) for result in result_dict]

    def signatureHelp(
        self,
        textDocument: TextDocumentIdentifier,
        position: Position,
        workDoneToken: Optional[str] = None,
        partialResultToken: Optional[str] = None,
    ) -> SignatureHelp | None:
        """
        The signature help request is sent from the client to the server to request signature information at a given cursor position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document.
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/signatureHelp", textDocument=textDocument, position=position
        )
        return SignatureHelp.model_validate(result_dict) if result_dict else None

    def completion(
        self,
        textDocument: TextDocumentIdentifier,
        position: Position,
        context: CompletionContext,
    ) -> list[CompletionItem] | CompletionList:
        """
        The signature help request is sent from the client to the server to request signature information at a given cursor position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document.
        :param CompletionContext context: The completion context. This is only available if the client specifies
                             CompletionContext               to send this using `ClientCapabilities.textDocument.completion.contextSupport === true`
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/completion",
            textDocument=textDocument,
            position=position,
            context=context,
        )
        if "isIncomplete" in result_dict:
            return CompletionList.model_validate(result_dict)

        return [CompletionItem.model_validate(result) for result in result_dict]

    def declaration(
        self, textDocument: TextDocumentIdentifier, position: Position
    ) -> Location | list[Location] | list[LocationLink] | None:
        """
        The go to declaration request is sent from the client to the server to resolve the declaration location of a
        symbol at a given text document position.

        The result type LocationLink[] got introduce with version 3.14.0 and depends in the corresponding client
        capability `clientCapabilities.textDocument.declaration.linkSupport`.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document.
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/declaration", textDocument=textDocument, position=position
        )
        if result_dict is None:
            return None

        if "uri" in result_dict:
            return Location.model_validate(result_dict)

        try:
            return [Location.model_validate(result) for result in result_dict]
        except ValidationError:
            return [LocationLink.model_validate(result) for result in result_dict]

    def definition(
        self,
        textDocument: TextDocumentIdentifier,
        position: Position,
        workDoneToken: Optional[str] = None,
        partialResultToken: Optional[str] = None,
    ) -> Location | list[Location] | list[LocationLink] | None:
        """
        The go to definition request is sent from the client to the server to resolve the declaration location of a
        symbol at a given text document position.

        The result type LocationLink[] got introduce with version 3.14.0 and depends in the corresponding client
        capability `clientCapabilities.textDocument.declaration.linkSupport`.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document.
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/definition", textDocument=textDocument, position=position
        )
        if result_dict is None:
            return None

        if "uri" in result_dict:
            return Location.model_validate(result_dict)

        try:
            return [Location.model_validate(result) for result in result_dict]
        except ValidationError:
            return [LocationLink.model_validate(result) for result in result_dict]

    def rename(self, text_document: TextDocumentIdentifier, position: Position, new_name: str) -> WorkspaceEdit:
        """Send a rename request to the language server at the specified position."""
        response = self.lsp_endpoint.call_method(
            "textDocument/rename",
            textDocument=text_document,
            position=position.dict(),
            newName=new_name,
        )

        # Parse response into WorkspaceEdit using Pydantic
        changes = {
            uri: [
                TextEdit(
                    range_start=Position(**edit["range"]["start"]),
                    range_end=Position(**edit["range"]["end"]),
                    new_text=edit["newText"]
                )
                for edit in edits
            ]
            for uri, edits in response.get("changes", {}).items()
        }
        return WorkspaceEdit(changes=changes)

    def references(
        self,
        textDocument: TextDocumentIdentifier,
        position: Position,
        context: ReferenceContext
    ) -> list[Location]:
        """
        The references request is sent from the client to the server to resolve project-wide references for the symbol denoted by the given text document position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document.
        :param ReferenceContext context:
        """

        result_raw = self.lsp_endpoint.call_method(
            "textDocument/references", textDocument=textDocument, position=position, context=context
        )
        return [Location.model_validate(result) for result in result_raw]
