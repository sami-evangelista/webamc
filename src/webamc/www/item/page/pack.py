from webamc.www.all import *
from webamc.www.item import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_item_t]
) -> he.Element:
    buttons = [
        he.Button(
            he.Str("all"),
            class_="px-4 py-2 bg-blue-500 rounded",
            onclick="pack_add_filter('all')",
            title="Récupérer toutes les questions"
        ),
        he.Button(
            he.Str("shuf"),
            class_="px-4 py-2 bg-[#00ff9B] rounded",
            onclick="pack_add_filter('shuf')",
            title="Mélanger les questions"
        ),
        he.Button(
            he.Str("head"),
            class_="px-4 py-2 bg-[#ffc300] rounded",
            onclick="pack_add_filter('head')",
            title="Choisir un certain nombre de questions",
        ),
        he.Button(
            he.Str("difficulty"),
            class_="px-4 py-2 bg-[#ff5733] rounded",
            onclick="pack_add_filter('with-difficulty')",
            title="Choisir la difficulté",
        ),
        he.Button(
            he.Str("code"),
            class_="px-4 py-2 bg-purple-500 rounded",
            onclick="pack_add_filter('with-code')",
            title="Choisir le code du QCM",
        ),
        he.Button(
            he.Str("tag"),
            class_="px-4 py-2 bg-blue-700 rounded",
            onclick="pack_add_filter('with-tag')",
            title="Choisir les tags des questions",
        ),
        he.Button(
            he.Str("sort"),
            class_="px-4 py-2 bg-[#ff0080] rounded",
            onclick="pack_add_filter('sort')",
            title="Trier les questions en fonctions du code ou de la difficulté",
        )
    ]
    div_add_filter_buttons = he.Div(
        *buttons,
        class_="flex flex-wrap gap-2 mb-4"
    )

    div_filters_container = he.Div(
        id_="filtersContainer",
        draggable="true",
        class_="min-h-[100px] p-4 bg-gray-200 rounded mb-4"
    )
    button7 = he.Button(
        he.Str("Réinitialiser"),
        onclick="pack_reset_filters()",
        class_="px-4 py-2 bg-gray-500 rounded"
    )
    button8 = he.Button(
        he.Str("Afficher le JSON"),
        onclick="pack_show_json_area()",
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
        class_="px-4 py-2 bg-green-500 rounded cursor-pointer hover:bg-green-600"
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
    button9 = he.Button(
        he.Str("Générer"),
        onclick="pack_download_json()",
        id="download_button",
        disabled=True,
        class_="px-4 py-2 bg-green-500 rounded disabled:bg-[#cccccc] disabled:border-[#999999] disabled:text-[#666666]"
    )
    button10 = he.Button(
        he.Str("Sauvegarder"),
        id="save_button",
        disabled=True,
        class_="px-4 py-2 bg-red-500 rounded disabled:border-[#999999] disabled:bg-[#cccccc] disabled:text-[#666666]"
    )

    div4 = he.Div(
        label,
        file_input,
        label2,
        file_input2,
        button7,
        button8,
        button9,
        button10,
        class_="flex mt-4 gap-3"
    )

    main_div = he.Div(
        div_add_filter_buttons,
        div_filters_container,
        pre,
        div4,
        class_="max-w-4xl p-6 rounded-lg shadow-lg box"
    )

    srcs = [
        "https://cdn.jsdelivr.net/npm/sweetalert2@11"
    ]
    scripts = [he.Script(src=src) for src in srcs]
    scripts.append(he.Script("pack_init()"))

    return he.ElementList(main_div, *scripts)
