<template>
    <MiniDialog v-model="model" title="Add new evidence" @cancel="cancel" @submit="saveNewEvidence" min-width="1000" close-icon>
        <template v-slot:text>
            <div class="d-flex" v-if="item">
                <v-sheet min-width="400" class="mr-1 ml-1">
                    <v-text-field :model-value="item.name"
                        readonly
                        disabled
                        density="compact"
                        label="Game title"
                        hide-details
                        hide-spin-buttons/>
                    <v-select v-model="tagId"
                        class="mt-2"
                        density="compact"
                        label="Associated tag"
                        :items="tagSelectData"
                        item-title="nameNum"
                        item-value="id"
                        hide-details
                        hide-spin-buttons/>
                    <v-textarea v-model="desc"
                        class="mt-2"
                        density="compact"
                        label="Evidence description"
                        hide-details
                        hide-spin-buttons/>
                    <v-file-input v-model="file"
                        accept="image/*"
                        label="Upload a matching image"
                        density="compact"
                        class="mt-2"
                        hide-details
                        hide-spin-buttons
                        @update:model-value="readFile"/>
                </v-sheet>
                <v-img class="pa-1 ml-2"
                    :src="image ? 'evidence/'+image : imagePreview"
                    :lazy-src="imgUrl"
                    alt="Image Preview"
                    height="300"/>
            </div>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { computed, ref, watch } from 'vue';
    import { useApp } from '@/store/app';
    import { useLoader } from '@/use/loader';
    import { useToast } from 'vue-toastification';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import { v4 as uuidv4 } from 'uuid';

    import imgUrl from '@/assets/__placeholder__.png';
    import DM from '@/use/data-manager';
    import { storeToRefs } from 'pinia';
    import { useTimes } from '@/store/times';

    const model = defineModel();
    const props = defineProps({
        item: {
            type: Object,
        },
        tag: {
            type: Number,
        },
        image: {
            type: String,
        }
    })

    const emit = defineEmits(["cancel", "submit"])

    const app = useApp();
    const times = useTimes()
    const toast = useToast();
    const loader = useLoader();

    const { currentCode } = storeToRefs(app);

    const desc = ref("");
    const tagId = ref(props.tag ? props.tag : null);
    const file = ref(null)
    const imagePreview = ref("")

    const evidence = ref(readEvidence())
    const tagSelectData = computed(() => {
        if (!props.item) return []
        // const set = new Set(props.item.tags.map(d => d.tag_id))
        // const added = new Set();
        return props.item.allTags.map(d => {
            const obj = Object.assign({}, d)
            obj.num = 0;
            evidence.value.forEach(e => {
                if (e.tag_id && e.tag_id === d.id) {
                    obj.num++;
                }
            })
            obj.nameNum = `${obj.name} (${obj.num})`
            // added.add(d.id)
            return obj;
        })
        // set.forEach(id => {
        //     if (!added.has(id)) {
        //         const obj = Object.assign({}, DM.getDataItem("tags", id))
        //         obj.num = 0;
        //         evidence.value.forEach(e => {
        //             if (e.tag_id && e.tag_id === id) {
        //                 obj.num++;
        //             }
        //         })
        //         obj.nameNum = `${obj.name} (${obj.num})`
        //         added.add(id)
        //         array.push(obj)
        //     }
        // })
        // return array;
    });

    function cancel() {
        model.value = false;
        emit("cancel")
    }
    function readEvidence() {
        if (props.item) {
            evidence.value = DM.getDataBy("evidence", d => d.game_id === props.item.id && d.code_id === currentCode.value)
        }
    }
    function readFile() {
        if (!file.value) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value);
    }
    async function saveNewEvidence() {
        if (!tagId.value) {
            return toast.error("missing related tag")
        }

        if (!props.image && !file.value && !desc.value) {
            return toast.error("need either a description or image")
        }

        const obj = {
            game_id: props.item.id,
            code_id: currentCode.value,
            description: desc.value,
            tag_id: tagId.value,
            created: Date.now(),
            created_by: app.activeUserId
        }

        if (props.image) {
            obj.filepath = props.image
        }

        if (!props.image && file.value) {
            const name = uuidv4();
            await loader.postImage(`image/evidence/${name}`, file.value);
            obj.filename = name;
        }

        await loader.post("add/evidence", { rows: [obj] })
        times.needsReload("evidence")
        toast.success("added evidence");
        file.value = null;
        imagePreview.value = "";
        model.value = false;
        emit("submit")
    }

    watch(props, () => {
        file.value = null;
        imagePreview.value = "";
        desc.value = ""
        tagId.value = props.tag ? props.tag : null
        readEvidence()
    }, { deep: true })

    watch(() => [times.datatags, times.evidence], readEvidence)

</script>