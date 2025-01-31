<template>
    <div style="text-align: left;">
        <div class="d-flex mb-1">
            <v-text-field
                v-model="name"
                density="compact"
                label="project name"
                class="mr-1"
                @update:model-value="update"
                hide-details
                hide-spin-buttons/>
            <v-text-field
                v-model="itemName"
                density="compact"
                label="items name"
                class="mr-1"
                @update:model-value="update"
                hide-details
                hide-spin-buttons/>
            <v-text-field
                v-model="metaItemName"
                density="compact"
                label="meta items name"
                @update:model-value="update"
                hide-details
                hide-spin-buttons/>
        </div>

        <v-textarea
            v-model="desc"
            density="compact"
            label="project description"
            class="mb-1"
            @update:model-value="update"
            hide-details
            hide-spin-buttons/>

        <v-divider class="mt-2 mb-2"></v-divider>

        <v-text-field
            v-model="codeName"
            density="compact"
            label="first code name"
            class="mb-1"
            @update:model-value="update"
            hide-details
            hide-spin-buttons/>

        <v-textarea
            v-model="codeDesc"
            density="compact"
            label="first code description"
            class="mb-1"
            @update:model-value="update"
            hide-details
            hide-spin-buttons/>

        <v-divider class="mt-2 mb-2"></v-divider>

        <div>select from existing users</div>

        <div class="d-flex mb-2 mt-1">
            <v-chip v-for="(u, i) in app.globalUsers"
                :class="i > 0 ? 'pa-2 mr-1' : 'pa-2 mr-1 ml-1'"
                :color="selectUsers.has(u.id) ? u.color : 'default'"
                @click="toggleUser(u.id)"
                variant="flat"
                size="small"
                density="compact">
                {{ u.name }}
            </v-chip>
        </div>

        <v-divider class="mt-2 mb-2"></v-divider>

        <v-checkbox
            v-model="hasScheme"
            label="additional data fields per item"
            density="compact"
            @update:model-value="update"
            hide-details
            hide-spin-buttons
            class="mb-1"/>

        <div v-if="hasScheme">
            <div v-for="(c, i) in columns" :key="'column_'+i" class="mt-2">

                <v-divider v-if="i > 0" class="mt-2 mb-2"></v-divider>
                <div class="d-flex justify-start align-start">
                    <v-btn
                        icon="mdi-delete"
                        class="mr-2"
                        color="error"
                        density="compact"
                        variant="plain"
                        rounded="sm"
                        hide-details
                        hide-spin-buttons
                        @click="removeColumn(i)"/>

                    <div style="width: 95%">
                        <div class="d-flex mb-1" >
                            <v-text-field
                                v-model="c.name"
                                density="compact"
                                label="name"
                                class="mr-1"
                                @update:model-value="update"
                                hide-details
                                hide-spin-buttons/>
                            <v-text-field
                                v-model="c.description"
                                density="compact"
                                label="description"
                                class="mr-1"
                                @update:model-value="update"
                                hide-details
                                hide-spin-buttons/>
                            <v-select
                                v-model="c.type"
                                density="compact"
                                label="data type"
                                :items="DATA_TYPES"
                                @update:model-value="update"
                                hide-details
                                hide-spin-buttons/>
                        </div>
                        <div class="d-flex">
                            <v-checkbox
                                v-model="c.required"
                                label="* required"
                                density="compact"
                                @update:model-value="update"
                                hide-details
                                hide-spin-buttons
                                class="mr-1"/>
                            <v-checkbox
                                v-model="c.has_default"
                                label="default value"
                                density="compact"
                                @update:model-value="update"
                                hide-details
                                hide-spin-buttons
                                class="mr-1"/>
                            <v-text-field v-if="c.has_default"
                                v-model="c.default_value"
                                density="compact"
                                label="default value"
                                @update:model-value="update"
                                hide-details
                                hide-spin-buttons/>
                        </div>
                    </div>
                </div>

            </div>
            <v-btn style="float: right"
                class="mt-2"
                color="secondary"
                density="comfortable"
                prepend-icon="mdi-plus"
                hide-details
                hide-spin-buttons
                @click="addColumn"
                >
                add data field
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { onMounted, reactive, ref } from 'vue';
    import { useToast } from 'vue-toastification';
    import { useApp } from '@/store/app';

    const app = useApp()
    const toast = useToast()

    const emit = defineEmits(["update"])

    const name = ref("")
    const desc = ref("")
    const itemName = ref("")
    const hasScheme = ref(false)

    const selectUsers = reactive(new Set())

    const metaItemName = ref("")

    const codeName = ref("")
    const codeDesc = ref("")

    const columns = ref([])
    const DATA_TYPES = ["string", "integer", "float", "date"]

    function isValid() {
        if (name.value.length === 0 || desc.value.length === 0) {
            return false
        }
        if (codeName.value.length === 0 || codeDesc.value.length === 0) {
            return false
        }
        if (itemName.value.length === 0 || metaItemName.value.length === 0) {
            return false
        }
        if (selectUsers.size === 0) {
            return false
        }
        if (hasScheme.value && columns.value.length > 0) {
            for (let i = 0; i < columns.value.length; ++i) {
                const c = columns.value[i];
                if (c.name.length === 0) {
                    return false
                }
                if (columns.value.some((d, j) => i !== j && d.name === c.name)) {
                    return false
                }
            }
        }
        return true
    }
    function makeDataset(validate=true) {
        const obj = {
            name: name.value,
            description: desc.value,
            code_name: codeName.value,
            code_desc: codeDesc.value,
            user_id: app.activeUserId,
            users: Array.from(selectUsers.values()),
            scheme: {
                item_name: itemName.value,
                meta_item_name: metaItemName.value,
                columns: []
            }
        }

        if (hasScheme.value && columns.value.length > 0) {
            const cols = []
            for (let i = 0; i < columns.value.length; ++i) {
                const c = columns.value[i];
                if (validate && c.name.length === 0) {
                    toast.error("missing data field name")
                    return null
                }
                if (validate && columns.value.some((d, j) => i !== j && d.name === c.name)) {
                    toast.error(`duplicate data field name "${c.name}"`)
                    return null
                }
                const tmp = Object.assign({}, c)
                delete tmp.min_value
                delete tmp.max_value
                delete tmp.has_default
                delete tmp.default_value

                if (c.has_default) {
                    switch(tmp.type) {
                        case "date":
                        case "integer":
                            tmp.default_value = Number.parseInt(c.default_value)
                            break;
                        case "float":
                            tmp.default_value = Number.parseFloat(c.default_value)
                            break;
                        default:
                            tmp.default_value = "" + c.default_value
                    }
                }
                cols.push(tmp)
            }
            obj.scheme.columns = cols
        }
        return obj
    }

    function reset() {
        name.value = ""
        desc.value = ""
        itemName.value = ""
        metaItemName.value = ""
        codeName.value = ""
        codeDesc.value = ""
        selectUsers.clear()
        hasScheme.value = false
        columns.value = []
    }
    function update() {
        emit("update", makeDataset(false))
    }

    function addColumn() {
        columns.value.push({
            name: "",
            type: "string",
            description: "",
            required: false,
            has_default: false,
            default_value: null,
            min_value: null,
            max_value: null
        })
        update()
    }
    function removeColumn(idx) {
        if (idx >= 0 && idx < columns.value.length) {
            columns.value.splice(idx, 1)
            update()
        }
    }

    function toggleUser(id) {
        if (selectUsers.has(id)) {
            selectUsers.delete(id)
        } else {
            selectUsers.add(id)
        }
        update()
    }

    defineExpose({ makeDataset, isValid })

    onMounted(reset)

</script>