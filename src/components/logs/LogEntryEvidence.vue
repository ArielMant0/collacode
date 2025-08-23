<template>
    <div>
        <div v-if="many">
            <div v-for="e in data">
                <div class="d-flex align-start">
                    <div>
                        <ItemTeaser v-if="e.item" :id="e.item.id" :width="120" :height="60"/>
                        <EvidenceIcon :type="e.type" class="mr-1" prevent-click/>
                        <b><TagText v-if="e.tag" :id="e.tag.id"/></b>
                    </div>
                    <ImgOrVideoCell v-if="e.filepath"
                        class="ml-4"
                        :path="e.filepath"
                        media-type="evidence"/>
                </div>
                <div>{{ e.description }}</div>
            </div>
        </div>
        <div v-else>
            <div class="d-flex align-start">
                <div>
                    <ItemTeaser v-if="data.item" :id="data.item.id" :width="120" :height="60"/>
                    <EvidenceIcon :type="data.type" class="mr-1" prevent-click/>
                    <b><TagText v-if="data.tag" :id="data.tag.id"/></b>
                </div>
                <ImgOrVideoCell v-if="data.filepath"
                    class="ml-4"
                    :path="data.filepath"
                    media-type="evidence"/>
            </div>
            <div>{{ data.description }}</div>
        </div>
    </div>
</template>

<script setup>
    import { computed } from 'vue';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import TagText from '../tags/TagText.vue';
    import ImgOrVideoCell from '../ImgOrVideoCell.vue';
import EvidenceIcon from '../evidence/EvidenceIcon.vue';

    const props = defineProps({
        data: {
            type: [Object, Array],
            required: true
        }
    })

    const many = computed(() => Array.isArray(props.data))

</script>