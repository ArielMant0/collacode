<template>
    <v-sheet class="pa-1" :color="selected ? 'secondary' : 'default'">
        <div style="position: relative;" :title="item.description">
            <v-btn v-if="allowEdit"
                icon="mdi-close"
                density="comfortable"
                size="x-small"
                class="red-on-hover pa-0"
                @click="deleteEvidence"
                style="position: absolute; right: -8px; top: -8px; z-index: 3999;"/>
            <v-img
                class="cursor-pointer"
                :src="item.filepath ? 'evidence/'+item.filepath : imgUrlS"
                @click.stop="emit('select', item)"
                v-ripple.center
                cover
                :width="height-10"
                :height="height-10"/>
        </div>
        <div v-if="tagName" class="text-caption text-dots" :style="{ 'max-width': (height-5)+'px' }" :title="tagName">
            {{ tagName }}
        </div>
    </v-sheet>
</template>

<script setup>

    import { computed } from 'vue';
    import { useLoader } from '@/use/loader';
    import { useToast } from "vue-toastification";
    import { useTimes } from '@/store/times';

    import imgUrlS from '@/assets/__placeholder__s.png'

    const times = useTimes()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        allowedTags: {
            type: Array,
            required: true
        },
        selected: {
            type: Boolean,
            default: false
        },
        allowEdit: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 80
        },
        scaleFactor: {
            type: Number,
            default: 4
        },
    })
    const emit = defineEmits(["select", "delete"])

    const loader = useLoader();
    const toast = useToast();

    const tagName = computed(() => {
        if (props.item.tag_id && props.allowedTags.length > 0) {
            const tag = props.allowedTags.find(d => d.id === props.item.tag_id);
            return tag ? tag.name : null
        }
        return null
    })

    async function deleteEvidence() {
        if (!props.allowEdit) return;
        await loader.post("delete/evidence", { ids: [props.item.id] })
        emit("delete", props.item.id)
        toast.success("deleted 1 evidence");
        times.needsReload("evidence")
    }

</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
.tiny-font {
    font-size: 10px;
    max-height: 200px;
}
.red-on-hover:hover {
    background-color: #b61431;
    color: white;
}
</style>