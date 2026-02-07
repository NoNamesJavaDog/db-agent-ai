import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { chatApi } from '../../api/chat';

interface Props {
  sessionId: number;
}

export default function FileUploader({ sessionId }: Props) {
  const { t } = useTranslation();

  const handleUpload = async (file: File) => {
    try {
      await chatApi.upload(sessionId, file);
      message.success(`${file.name} uploaded`);
    } catch {
      message.error('Upload failed');
    }
    return false; // prevent default upload
  };

  return (
    <Upload
      beforeUpload={handleUpload}
      showUploadList={false}
      accept=".sql,.txt,.csv,.json,.md"
    >
      <Button icon={<UploadOutlined />} size="small">
        {t('chat.uploadFile')}
      </Button>
    </Upload>
  );
}
