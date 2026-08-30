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
                <v-progress-circular indeterminate></v-progress-circular>
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
                <v-btn
                    :prepend-icon="editNotes ? (noteChanges ? 'mdi-sync' : 'mdi-cancel') : 'mdi-pencil'"
                    :color="editNotes && noteChanges ? 'primary' : 'default'"
                    size="small"
                    density="comfortable"
                    variant="tonal"
                    @click="toggleEdit"
                    >
                    {{ editNotes ? (noteChanges ? "save" : "cancel") : "edit" }}
                </v-btn>
            </div>
            
            <v-textarea
                v-if="editNotes"
                v-model="noteText"
                density="compact"
                :rows="numRows"
                style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif; font-size: small;"
                variant="outlined"
                placeholder="add notes here..."
                />
            <v-sheet v-else
                v-html="notesMD"
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
    import { computed, onBeforeUnmount, onMounted, toRaw, watch } from 'vue';
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

    const numRows = computed(() => Math.max(5, countChar(noteText.value, "\n")+1))

    function countChar(str, char){
    	return [...str].filter(i => i === char).length
    }

    function toggleEdit() {
        if (editNotes.value) {
            saveNotes()
        } else {
            startEdit()
        }
    }

    async function saveNotes() {
        if (noteChanges.value) {
            try {
                saving.value = true
                const obj = Object.assign({}, toRaw(props.item.notes))
                obj.text = noteText.value
                await addUpdateItemNotes([obj])
                toast.success("updated notes for " + props.item.name)
                times.needsReload("item_notes")
            } catch (e) {
                console.error(e.toString())
                toast.error("error saving notes")
            }
            
        }
        editNotes.value = false
        saving.value = false
    }

    function startEdit() {
        if (!editNotes.value) {
            saving.value = false
            editNotes.value = true
        }
    }

    function read() {
        if (noteChanges.value) {
            saveNotes()
        }
        editNotes.value = false
        initialNote.value = props.item.notes?.text
        noteText.value = initialNote.value
    }

    function init() {
        read()
        if (saveInterval !== null) {
            clearInterval(saveInterval)
        }
        saveInterval = setInterval(saveNotes, 120000) // save notes every 2 min
    }

    onMounted(init)
    onBeforeUnmount(function() {
        if (saveInterval !== null) {
            clearInterval(saveInterval)
        }
    })

    watch(() => props.item.id, read)
    watch(() => times.item_notes, function() {
        editNotes.value = false
        initialNote.value = props.item.notes?.text
        noteText.value = initialNote.value
    })

</script>

<style>
    .markdown ul, .markdown ol {
        list-style-position: inside;
    }
</style>