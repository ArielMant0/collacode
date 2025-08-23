<template>
    <div>
        <div v-if="many">
            <div v-for="d in data">
                <ItemTeaser v-if="d.item" :id="d.item.id" :width="120" :height="60"/>
                <ItemTeaser v-else-if="d.item_id" :id="d.item_id" :width="120" :height="60"/>
                <TagText v-if="d.tag" :id="d.tag.id"/>
                <TagText v-else-if="d.tag_id" :id="d.tag_id"/>
            </div>
        </div>
        <div v-else>
            <ItemTeaser v-if="data.item" :id="d.item.id" :width="120" :height="60"/>
            <ItemTeaser v-else-if="data.item_id" :id="d.item_id" :width="120" :height="60"/>
            <TagText v-if="data.tag" :id="d.tag.id"/>
            <TagText v-else-if="data.tag_id" :id="d.tag_id"/>
        </div>
    </div>
</template>

<script setup>
    import { computed } from 'vue';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import TagText from '../tags/TagText.vue';

    const props = defineProps({
        data: {
            type: [Object, Array],
            required: true
        }
    })

    const many = computed(() => Array.isArray(props.data))


</script>