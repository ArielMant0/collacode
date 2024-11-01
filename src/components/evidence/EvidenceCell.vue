<template>
    <v-sheet class="pa-1" :color="selected ? 'secondary' : 'default'">
        <div style="position: relative;" :title="item.description">
            <v-btn v-if="allowCopy"
                icon="mdi-content-copy"
                density="comfortable"
                size="small"
                class="primary-on-hover"
                @click="copyEvidence"
                style="position: absolute; right: 24px; top: -8px; z-index: 3999;"/>
            <v-btn v-if="allowEdit"
                icon="mdi-close"
                density="comfortable"
                size="small"
                class="red-on-hover pa-0"
                @click="deleteEvidence"
                style="position: absolute; right: -8px; top: -8px; z-index: 3999;"/>
            <v-img
                class="cursor-pointer"
                :src="item.filepath ? 'evidence/'+item.filepath : imgUrlS"
                @click.stop="emit('select', item)"
                @contextmenu.stop="onRightClick"
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
    import { useSettings } from '@/store/settings';
    import { useApp } from '@/store/app';

    const app = useApp()
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
        allowCopy: {
            type: Boolean,
            default: false
        },
        disableContextMenu: {
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
    const emit = defineEmits(["select", "delete", "right-click"])

    const loader = useLoader();
    const toast = useToast();
    const settings = useSettings();

    const tagName = computed(() => {
        if (props.item.tag_id && props.allowedTags.length > 0) {
            const tag = props.allowedTags.find(d => d.id === props.item.tag_id);
            return tag ? tag.name : null
        }
        return null
    })

    function onRightClick(event) {
        emit("right-click", props.item)
        event.preventDefault();
        if (props.disableContextMenu) return;
        settings.setRightClick(
            props.item.game_id,
            props.item.tag_id,
            props.item.id,
            event.pageX + 15,
            event.pageY + 15,
            ["add externalization"]
        );
    }

    function copyEvidence() {
        app.toggleAddEvidence(props.item.game_id, null, props.item.filepath)
    }

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
</style>