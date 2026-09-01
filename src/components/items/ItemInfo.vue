<template>
    <div
        :style="{
            minWidth: minW,
            width: w,
            maxHeight: maxH,
            overflowY: 'auto'
        }"
        class="pa-2">

        <div class="text-caption" style="max-height: 200px; overflow-y: auto;">
            <div><b>Name</b>: {{ item.name }}</div>
            <div v-if="item.url"><b>URL</b>: <a :href="item.url" target="_blank">{{ item.url }}</a></div>
    
            <div v-for="c in app.schema.columns" :key="'col_'+c.name" class="mt-1">
                <b>{{ capitalize(c.name) }}</b>: {{ item[c.name] }}
            </div>
    
            <div v-if="item.description" class="mt-1 mb-1">
                <b>Description</b>
                <p>{{ item.description }}</p>
            </div>
        </div>

        <div>

            <v-divider class="mt-2 mb-2"></v-divider>
            
            <div v-if="saving" class="d-flex text-caption">
                <v-progress-circular indeterminate size="16" width="2"></v-progress-circular>
                <span class="ml-1">saving changes...</span>
            </div>
            <div v-else class="d-flex justify-space-between text-caption mb-1">
                <div  class="d-flex text-caption">
                    <v-icon
                        :icon="noteChanges ? 'mdi-alert-circle' : 'mdi-check-circle'"
                        :color="noteChanges ? 'error' : 'primary'"
                        size="small"
                        />
                    <span class="ml-1">
                        {{ noteChanges ? 'unsaved changes' : 'up to date' }}
                    </span>
                </div>
                <div class="d-flex">
                    <v-btn v-if="noteChanges"
                        icon="mdi-sync"
                        color="primary"
                        size="small"
                        rounded="sm"
                        density="compact"
                        variant="tonal"
                        class="mr-1"
                        @click="saveNotes"
                        >
                    </v-btn>
                    <v-btn
                        :icon="editNotes ? 'mdi-eye' : 'mdi-pencil'"
                        color="default"
                        size="small"
                        rounded="sm"
                        density="compact"
                        variant="tonal"
                        class="ml-1"
                        @click="toggleEdit(true)"
                        >
                    </v-btn>
                </div>
            </div>
            
            <v-textarea
                v-if="editNotes"
                ref="editor"
                v-model="noteText"
                density="compact"
                :rows="numRows"
                @blur="toggleEdit(true)"
                style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif; font-size: small;"
                variant="outlined"
                placeholder="add notes here..."
                />
            <v-sheet v-else
                v-html="notesMD"
                @click="toggleEdit(false)"
                class="pa-2 markdown"
                min-height="100px"
                border
                rounded
                >
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { addUpdateItemNotes } from '@/use/data-api';
    import { capitalize } from '@/use/utility';
    import { marked } from 'marked';
    import { computed, onBeforeUnmount, onMounted, toRaw, useTemplateRef, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        minWidth: {
            type: [String, Number],
            default: "200px"
        },
        width: {
            type: [String, Number],
            default: "auto"
        },
        maxHeight: {
            type: [String, Number],
            default: "90vh"
        }
    })

    const editor = useTemplateRef("editor")

    let saveInterval = null
    const saving = ref(false)
    const editNotes = ref(false)
    const initialNote = ref("")
    const noteText = ref("")
    const noteChanges = computed(() => initialNote.value !== noteText.value)
    const notesMD = computed(() => noteText.value ? marked.parse(noteText.value) : "")

    const minW = computed(() => typeof props.minWidth === "number" ? props.minWidth+'px' : props.minWidth)
    const w = computed(() => typeof props.width === "number" ? props.width+'px' : props.width)
    const maxH = computed(() => typeof props.maxHeight === "number" ? props.maxHeight+'px' : props.maxHeight)

    const numRows = computed(() => Math.max(5, countLines(noteText.value) + 1))

    function countLines(str) {
        const matches = str.match(/\n/g)
        return matches ? matches.length : 0
    }

    function toggleEdit(save=true) {
        editNotes.value = !editNotes.value
        if (editNotes.value && editor.value) {
            editor.value.focus()
        }
        if (save) {
            saveNotes()
        }
    }

    async function saveNotes() {
        if (noteChanges.value) {
            try {
                saving.value = true
                const obj = Object.assign({}, toRaw(props.item.notes))
                obj.text = noteText.value
                await addUpdateItemNotes([obj])
                times.needsReload("item_notes")
            } catch (e) {
                console.error(e.toString())
                toast.error("error saving notes")
            }
        }
        saving.value = false
    }

    function read() {
        if (noteChanges.value) {
            saveNotes()
        }
        initialNote.value = props.item.notes?.text
        noteText.value = initialNote.value
    }

    function init() {
        read()
        if (saveInterval !== null) {
            clearInterval(saveInterval)
            saveInterval = null
        }
        saveInterval = setInterval(saveNotes, 120000) // save notes every 2 min
    }

    onMounted(init)
    onBeforeUnmount(function() {
        if (saveInterval !== null) {
            clearInterval(saveInterval)
            saveInterval = null
        }
    })

    watch(() => props.item.id, read)
    watch(() => times.item_notes, function() {
        initialNote.value = props.item.notes.text
    })

</script>

<style>
    .markdown {
        font-size: smaller;
    }
    .markdown ul, .markdown ol {
        list-style-position: inside;
    }
</style>