from webamc.www.all import *
from webamc.www.item import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_item_t]
) -> he.Element:
    """
    button7 = he.Button(
        he.Str("Afficher le JSON"),
        onclick="pack.show_json_area()",
        id_="showjson-button",
        class_="px-4 py-2 bg-gray-500 rounded"
    )

    # JSON display
    pre = he.Pre(
        id_="jsonOutput",
        class_="bg-gray-200 p-4 rounded overflow-x-auto mt-4"
    )
    label = he.Label(
        he.Str("Importer"),
        for_="import_button",
        class_=(
            "px-4 py-2 bg-green-500 rounded cursor-pointer "
            "hover:bg-green-600"
        )
    )
    file_input = he.Input(
        type_="file",
        id_="import_button",
        accept=".json",
        class_="hidden"
    )
    label2 = he.Label(
        he.Str("Ajouter"),
        for_="add_import_button",
        class_="px-4 py-2 bg-blue-500 rounded cursor-pointer hover:bg-blue-600"
    )
    file_input2 = he.Input(
        type="file",
        id="add_import_button",
        accept=".json",
        class_="hidden"
    )
    button8 = he.Button(
        he.Str("Générer"),
        onclick="pack.download_json()",
        id="download_button",
        disabled=True,
        class_=(
            "px-4 py-2 bg-green-500 rounded disabled:bg-[#cccccc] "
            "disabled:border-[#999999] disabled:text-[#666666]"
        )
    )
    button9 = he.Button(
        he.Str("Sauvegarder"),
        id="save_button",
        disabled=True,
        class_=(
            "px-4 py-2 bg-red-500 rounded disabled:border-[#999999] "
            "disabled:bg-[#cccccc] disabled:text-[#666666]"
        )
    )

    div4 = he.Div(
        label,
        file_input,
        label2,
        file_input2,
        button7,
        button8,
        button9,
        class_="flex mt-4 gap-3"
    )

    main_div = he.Div(
        div_filters_container,
        pre,
        div4,
        class_="max-w-4xl p-6 rounded-lg shadow-lg box"
    )
"""
    div_pack = he.Div(id_="div-pack")
    js = he.Script("new Pack('div-pack', 'pack');")
    return he.ElementList(div_pack, js)
