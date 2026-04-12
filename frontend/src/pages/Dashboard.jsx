import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiJson } from "@/services/api";
import { API_BASE } from "@/services/apiBase";

const ADMIN_ISSUES_QUERY_KEY = ["admin", "issues"];

function fetchAdminIssues() {
  return apiJson(`${API_BASE}/admin/issues`);
}

export default function Dashboard() {
  const [selectedImage, setSelectedImage] = useState(null);
  const isAdmin = localStorage.getItem("adminSession") === "true";
  const queryClient = useQueryClient();
  const { data: issues = [] } = useQuery({
    queryKey: ADMIN_ISSUES_QUERY_KEY,
    queryFn: fetchAdminIssues,
    placeholderData: (previous) => previous ?? [],
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }) => {
      const body = new URLSearchParams({ status });
      return apiJson(`${API_BASE}/admin/issues/${id}`, {
        method: "PUT",
        body,
      });
    },
    onMutate: async ({ id, status }) => {
      await queryClient.cancelQueries({ queryKey: ADMIN_ISSUES_QUERY_KEY });
      const previousIssues = queryClient.getQueryData(ADMIN_ISSUES_QUERY_KEY) || [];
      queryClient.setQueryData(
        ADMIN_ISSUES_QUERY_KEY,
        previousIssues.map((issue) => (issue.id === id ? { ...issue, status } : issue))
      );
      return { previousIssues };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousIssues) {
        queryClient.setQueryData(ADMIN_ISSUES_QUERY_KEY, context.previousIssues);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ADMIN_ISSUES_QUERY_KEY });
    },
  });

  const deleteIssueMutation = useMutation({
    mutationFn: async (id) => {
      return apiJson(`${API_BASE}/admin/issues/${id}`, {
        method: "DELETE",
      });
    },
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ADMIN_ISSUES_QUERY_KEY });
      const previousIssues = queryClient.getQueryData(ADMIN_ISSUES_QUERY_KEY) || [];
      queryClient.setQueryData(
        ADMIN_ISSUES_QUERY_KEY,
        previousIssues.filter((issue) => issue.id !== id)
      );
      return { previousIssues };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousIssues) {
        queryClient.setQueryData(ADMIN_ISSUES_QUERY_KEY, context.previousIssues);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ADMIN_ISSUES_QUERY_KEY });
    },
  });

  return (
    <div className="dashboard-container">
      <h2>Urban Sentinel Dashboard</h2>

      <div className="card-grid">
        {issues.map((issue) => (
          <div key={issue.id} className="issue-card">
            <h3>{issue.title}</h3>
            <p>{issue.description}</p>
            <p><strong>Complaint No:</strong> {issue.complaint_number}</p>
            <p><strong>Status:</strong> {issue.status}</p>

            {isAdmin && (
              <div className="admin-controls">
                <select
                  value={issue.status}
                  onChange={(e) => updateStatusMutation.mutate({ id: issue.id, status: e.target.value })}
                >
                  <option>Pending</option>
                  <option>In Progress</option>
                  <option>Resolved</option>
                </select>

                <button onClick={() => deleteIssueMutation.mutate(issue.id)}>
                  Delete
                </button>
              </div>
            )}

            <div className="image-grid">
              {issue.media?.split(",")?.map((img, i) => (
                <img key={i} src={img} alt="" onClick={() => setSelectedImage(img)} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {selectedImage && (
        <div className="modal" onClick={() => setSelectedImage(null)}>
          <img src={selectedImage} alt="" />
        </div>
      )}
    </div>
  );
}
