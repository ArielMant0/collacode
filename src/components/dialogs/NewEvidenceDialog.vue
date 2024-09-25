<template>
    <MiniDialog v-model="model" title="Add new evidence" @cancel="cancel" @submit="saveNewEvidence" min-width="1000">
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
                    :src="imagePreview"
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

    const model = defineModel();
    const props = defineProps({
        item: {
            type: Object,
        },
        tag: {
            type: Number,
        },
    })

    const emit = defineEmits(["cancel", "submit"])

    const app = useApp();
    const toast = useToast();
    const loader = useLoader();

    const { currentCode } = storeToRefs(app);

    const desc = ref("");
    const tagId = ref(props.tag ? props.tag : null);
    const file = ref([])
    const imagePreview = ref("")

    const evidence = computed(() => DM.getDataBy("evidence", d => d.game_id === props.item.id && d.code_id === currentCode.value))
    const tagSelectData = computed(() => {
        return props.item.allTags.map(d => {
            const obj = Object.assign({}, d)
            obj.num = 0;
            evidence.value.forEach(e => {
                if (e.tag_id && e.tag_id === d.id) {
                    obj.num++;
                }
            })
            obj.nameNum = `${obj.name} (${obj.num})`
            return obj;
        })
    });

    function cancel() {
        model.value = false;
        emit("cancel")
    }
    function readFile() {
        if (file.value.length === 0) {
            imagePreview.value = "";
            return;
        }

        const reader = new FileReader();
        reader.addEventListener('load', () => imagePreview.value = reader.result);
        reader.readAsDataURL(file.value[0]);
    }
    async function saveNewEvidence() {
        const obj = {
            game_id: props.item.id,
            code_id: currentCode.value,
            description: desc.value,
            tag_id: tagId.value,
            created: Date.now(),
            created_by: app.activeUserId
        }

        if (file.value && file.value[0]) {
            const name = uuidv4();
            await loader.postImage(`image/evidence/${name}`, file.value[0]);
            obj.filename = name;
        }

        await loader.post("add/evidence", { rows: [obj] })
        app.needsReload("evidence")
        toast.success("updated evidence");
        file.value = [];
        imagePreview.value = "";
        model.value = false;
        emit("submit")
    }

    watch(props, () => {
        file.value = [];
        imagePreview.value = "";
        desc.value = ""
        tagId.value = props.tag ? props.tag : null
    }, { deep: true })

</script>